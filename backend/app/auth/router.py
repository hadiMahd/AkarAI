import hashlib
import secrets
import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_actor,
    get_tenant_context,
    require_permission,
    require_role,
)
from app.auth.permissions import PermissionKey
from app.auth.schemas import (
    ActorSummary,
    AuthSessionResponse,
    CsrfTokenResponse,
    CurrentActorResponse,
    EmployeeDeactivationRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    SessionResponse,
    SessionRevocationRequest,
    TenantContextResponse,
)
from app.auth.service import AuthService, revoke_user_all_sessions
from app.auth.repository import AuthRepository
from app.auth.models import Role as RoleModel, Permission as PermissionModel, RolePermission
from app.audit.service import AuditService
from app.audit.repository import AuditLogRepository
from app.common.dependencies import get_db_session
from app.common.exceptions import AppException, RateLimitExceededError
from app.common.rate_limit import check_auth_rate_limit
from app.common.request_id import get_request_id
from app.agencies.service import AgenciesService
from app.agencies.repository import AgenciesRepository
from app.agencies.models import AgencyEmployeeMembership
from app.common.tenant import TenantContext
from app.users.models import User
from app.common.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])
tenant_router = APIRouter(prefix="/tenant", tags=["Tenant"])

CSRF_COOKIE_NAME = "akarai_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        httponly=settings.auth_cookie_httponly,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path=settings.auth_refresh_cookie_path,
        domain=settings.auth_cookie_domain,
        max_age=settings.jwt_refresh_ttl_days * 86400,
    )


def _set_csrf_cookie(response: Response, csrf_token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
        domain=settings.auth_cookie_domain,
        max_age=settings.jwt_refresh_ttl_days * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        path=settings.auth_refresh_cookie_path,
        domain=settings.auth_cookie_domain,
    )


def _clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
        domain=settings.auth_cookie_domain,
    )


def _get_refresh_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(settings.auth_refresh_cookie_name)


def _get_csrf_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(CSRF_COOKIE_NAME)


def _generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


async def _build_actor_summary(user: User, db: AsyncSession) -> ActorSummary:
    role_name = None
    perm_keys: list[str] = []

    if user.role_id:
        role_result = await db.execute(select(RoleModel).where(RoleModel.id == user.role_id))
        role = role_result.scalar_one_or_none()
        if role:
            role_name = role.slug
            perm_result = await db.execute(
                select(PermissionModel.key)
                .select_from(RolePermission)
                .join(PermissionModel, RolePermission.permission_id == PermissionModel.id)
                .where(RolePermission.role_id == user.role_id)
            )
            perm_keys = [row[0] for row in perm_result.all()]

    return ActorSummary(
        id=str(user.id),
        email=user.email,
        role=role_name or "user",
        permissions=perm_keys,
        is_active=user.is_active,
    )


async def verify_csrf_token(request: Request) -> None:
    cookie_token = _get_csrf_token_from_cookie(request)
    header_token = request.headers.get(CSRF_HEADER_NAME)

    if not cookie_token or not header_token:
        raise AppException(
            status_code=403,
            detail="CSRF token missing",
            error_code="CSRF_TOKEN_MISSING",
        )

    if not secrets.compare_digest(cookie_token, header_token):
        raise AppException(
            status_code=403,
            detail="CSRF token invalid",
            error_code="CSRF_TOKEN_INVALID",
        )


@router.get("/csrf-token", response_model=CsrfTokenResponse)
async def get_csrf_token(request: Request):
    csrf_token = _get_csrf_token_from_cookie(request)
    if not csrf_token:
        csrf_token = _generate_csrf_token()

    response = JSONResponse(content={"csrf_token": csrf_token})
    _set_csrf_cookie(response, csrf_token)
    return response


@router.post("/login", response_model=SessionResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    identifier = body.email
    if not await check_auth_rate_limit("login", identifier):
        raise RateLimitExceededError(detail="Too many login attempts. Try again later.")

    repo = AuthRepository(db)
    svc = AuthService(repo)

    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")

    result = await svc.login(body.email, body.password, ip_address=ip, user_agent=ua)

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)

    if result is None:
        await audit_svc.log_auth_event(
            action="auth.sign_in.failure",
            result="failure",
            request_id=get_request_id(request),
            ip_address=ip,
            user_agent=ua,
            metadata={"email": body.email},
        )
        raise AppException(status_code=401, detail="Invalid credentials", error_code="INVALID_CREDENTIALS")

    user = result["user"]

    await audit_svc.log_auth_event(
        action="auth.sign_in.success",
        result="success",
        actor_user_id=user.id,
        request_id=get_request_id(request),
        ip_address=ip,
        user_agent=ua,
    )

    actor = await _build_actor_summary(user, db)

    _set_refresh_cookie(response, result["refresh_token"])

    csrf_token = _generate_csrf_token()
    _set_csrf_cookie(response, csrf_token)

    return SessionResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        actor=actor,
    )


@router.post("/register", response_model=SessionResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    identifier = body.email
    if not await check_auth_rate_limit("register", identifier):
        raise RateLimitExceededError(detail="Too many registration attempts. Try again later.")

    repo = AuthRepository(db)
    svc = AuthService(repo)

    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")

    result = await svc.register(body.email, body.password, body.name, ip_address=ip, user_agent=ua)

    if result is None:
        raise AppException(status_code=409, detail="User with this email already exists", error_code="USER_EXISTS")

    user = result["user"]

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)

    await audit_svc.log_auth_event(
        action="auth.register.success",
        result="success",
        actor_user_id=user.id,
        request_id=get_request_id(request),
        ip_address=ip,
        user_agent=ua,
    )

    actor = await _build_actor_summary(user, db)

    _set_refresh_cookie(response, result["refresh_token"])

    csrf_token = _generate_csrf_token()
    _set_csrf_cookie(response, csrf_token)

    return SessionResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        actor=actor,
    )


# CSRF PROTECTION NOTE:
# This endpoint relies on SameSite cookie policy for CSRF protection (not explicit token validation).
# The refresh token is stored in an HttpOnly cookie with SameSite=lax, which prevents cross-site requests.
# If you change to SameSite=None (cross-site cookies) or a different deployment shape,
# you MUST add dependencies=[Depends(verify_csrf_token)] to this endpoint.
@router.post("/refresh", response_model=SessionResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    identifier = request.client.host if request.client else "unknown"
    if not await check_auth_rate_limit("refresh", identifier):
        raise RateLimitExceededError(detail="Too many refresh attempts. Try again later.")

    refresh_token = _get_refresh_token_from_cookie(request)

    if not refresh_token:
        raise AppException(
            status_code=401,
            detail="No refresh token provided",
            error_code="NO_REFRESH_TOKEN",
        )

    repo = AuthRepository(db)
    svc = AuthService(repo)

    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")

    result = await svc.refresh(refresh_token, ip_address=ip, user_agent=ua)

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)

    if result is None:
        await audit_svc.log_auth_event(
            action="auth.refresh.failure",
            result="failure",
            request_id=get_request_id(request),
            ip_address=ip,
            user_agent=ua,
        )
        raise AppException(status_code=401, detail="Invalid or expired refresh token", error_code="INVALID_REFRESH_TOKEN")

    user = result["user"]

    await audit_svc.log_auth_event(
        action="auth.refresh.success",
        result="success",
        actor_user_id=user.id,
        request_id=get_request_id(request),
        ip_address=ip,
        user_agent=ua,
    )

    actor = await _build_actor_summary(user, db)

    _set_refresh_cookie(response, result["refresh_token"])

    return SessionResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        actor=actor,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    repo = AuthRepository(db)
    svc = AuthService(repo)

    refresh_token = _get_refresh_token_from_cookie(request)

    await svc.logout(actor["user_id"], refresh_token)

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)
    await audit_svc.log_auth_event(
        action="auth.sign_out",
        result="success",
        actor_user_id=actor["user_id"],
        request_id=get_request_id(request) if request else None,
    )

    _clear_refresh_cookie(response)
    _clear_csrf_cookie(response)

    return None


@router.post("/password-reset", status_code=204)
async def password_reset(
    body: PasswordResetRequest,
    request: Request,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    identifier = actor["user_id"]
    if not await check_auth_rate_limit("password_reset", identifier):
        raise RateLimitExceededError(detail="Too many password reset attempts. Try again later.")

    repo = AuthRepository(db)
    svc = AuthService(repo)

    success = await svc.reset_password(actor["user_id"], body.current_password, body.new_password)

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)

    if not success:
        raise AppException(status_code=400, detail="Current password is incorrect", error_code="INVALID_PASSWORD")

    await audit_svc.log_auth_event(
        action="auth.password_reset",
        result="success",
        actor_user_id=actor["user_id"],
        request_id=get_request_id(request),
    )


@router.post("/sessions/{session_id}/revoke", status_code=204)
async def revoke_session(
    session_id: str,
    body: SessionRevocationRequest,
    request: Request,
    actor: dict = Depends(require_permission(PermissionKey.AUTH_SESSION_REVOKE)),
    db: AsyncSession = Depends(get_db_session),
):
    identifier = actor["user_id"]
    if not await check_auth_rate_limit("session_revoke", identifier):
        raise RateLimitExceededError(detail="Too many revocation attempts. Try again later.")

    repo = AuthRepository(db)
    svc = AuthService(repo)

    success = await svc.revoke_session(session_id, body.reason, actor["user_id"])

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)

    if not success:
        raise AppException(status_code=404, detail="Session not found or not accessible", error_code="SESSION_NOT_FOUND")

    await audit_svc.log_auth_event(
        action="auth.session_revoked",
        result="success",
        actor_user_id=actor["user_id"],
        request_id=get_request_id(request),
        metadata={"session_id": session_id, "reason": body.reason},
    )


@router.post("/employees/{membership_id}/deactivate", status_code=204)
async def deactivate_employee(
    membership_id: str,
    body: EmployeeDeactivationRequest,
    request: Request,
    actor: dict = Depends(require_permission(PermissionKey.AUTH_EMPLOYEE_DEACTIVATE)),
    db: AsyncSession = Depends(get_db_session),
):
    identifier = actor["user_id"]
    if not await check_auth_rate_limit("employee_deactivate", identifier):
        raise RateLimitExceededError(detail="Too many deactivation attempts. Try again later.")

    from uuid import UUID

    result = await db.execute(
        select(AgencyEmployeeMembership).where(AgencyEmployeeMembership.id == membership_id)
    )
    target_membership = result.scalar_one_or_none()

    if target_membership is None:
        raise AppException(status_code=404, detail="Membership not found", error_code="MEMBERSHIP_NOT_FOUND")

    agencies_repo = AgenciesRepository(db)
    agencies_svc = AgenciesService(agencies_repo)

    deactivated_by = UUID(actor["user_id"])
    await agencies_svc.deactivate_employee(target_membership, deactivated_by, body.reason)

    auth_repo = AuthRepository(db)
    auth_svc = AuthService(auth_repo)
    await revoke_user_all_sessions(auth_repo, str(target_membership.user_id), "employee_deactivation")

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)
    await audit_svc.log_auth_event(
        action="auth.employee_deactivated",
        result="success",
        actor_user_id=actor["user_id"],
        tenant_id=target_membership.agency_tenant_id,
        request_id=get_request_id(request),
        metadata={"membership_id": membership_id, "deactivated_user_id": str(target_membership.user_id), "reason": body.reason},
    )


@router.get("/me", response_model=CurrentActorResponse)
async def get_me(actor: dict = Depends(get_current_actor)):
    return CurrentActorResponse(
        actor=ActorSummary(
            id=actor["id"],
            email=actor["email"],
            role=actor.get("role") or "user",
            permissions=actor.get("permissions", []),
            is_active=actor.get("is_active", True),
        )
    )


@tenant_router.get("/context", response_model=TenantContextResponse)
async def get_tenant_context(
    ctx: TenantContext = Depends(get_tenant_context),
):
    return TenantContextResponse(
        actor_id=str(ctx.actor_id) if ctx.actor_id else "",
        role=ctx.role or "",
        permissions=ctx.permissions,
        tenant_id=str(ctx.tenant_id) if ctx.tenant_id else None,
        membership_id=str(ctx.membership_id) if ctx.membership_id else None,
        is_platform_actor=ctx.is_platform_actor,
    )
