from fastapi import APIRouter, Depends, HTTPException, Request
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
    CurrentActorResponse,
    EmployeeDeactivationRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetRequest,
    RefreshRequest,
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

router = APIRouter(prefix="/auth", tags=["Auth"])
tenant_router = APIRouter(prefix="/tenant", tags=["Tenant"])


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


@router.post("/login", response_model=AuthSessionResponse)
async def login(
    body: LoginRequest,
    request: Request,
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
    return AuthSessionResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        actor=actor,
    )


@router.post("/refresh", response_model=AuthSessionResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    identifier = request.client.host if request.client else "unknown"
    if not await check_auth_rate_limit("refresh", identifier):
        raise RateLimitExceededError(detail="Too many refresh attempts. Try again later.")

    repo = AuthRepository(db)
    svc = AuthService(repo)

    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")

    result = await svc.refresh(body.refresh_token, ip_address=ip, user_agent=ua)

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
    return AuthSessionResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        actor=actor,
    )


@router.post("/logout", status_code=204)
async def logout(
    body: LogoutRequest | None = None,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
    request: Request = None,
):
    repo = AuthRepository(db)
    svc = AuthService(repo)
    await svc.logout(actor["user_id"], body.refresh_token if body else None)

    audit_repo = AuditLogRepository(db)
    audit_svc = AuditService(audit_repo)
    await audit_svc.log_auth_event(
        action="auth.sign_out",
        result="success",
        actor_user_id=actor["user_id"],
        request_id=get_request_id(request) if request else None,
    )


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
