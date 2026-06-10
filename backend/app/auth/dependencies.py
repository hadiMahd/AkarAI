from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.exceptions import UnauthorizedError, ForbiddenError
from app.common.security import decode_access_token
from app.common.tenant import TenantContext
from app.common.rls import apply_rls_context_from_tenant_context
from app.auth.permissions import PermissionKey
from app.auth.models import Role as RoleModel, Permission as PermissionModel, RolePermission
from app.auth.service import is_token_blacklisted, get_session_invalidation_timestamp
from app.common.redis import redis_get
from app.users.models import User
from app.agencies.models import AgencyEmployeeMembership
from app.common.dependencies import get_db_session


async def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        raise UnauthorizedError(detail="Missing or invalid Authorization header")
    return auth[7:]


async def get_current_actor(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    token = await _extract_token(request)
    try:
        payload = decode_access_token(token)
    except Exception:
        raise UnauthorizedError(detail="Invalid or expired access token")

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise UnauthorizedError(detail="Token has been revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(detail="Invalid token payload")

    invalidation_ts = await get_session_invalidation_timestamp(user_id)
    if invalidation_ts is not None:
        iat = payload.get("iat", 0)
        if iat < invalidation_ts:
            raise UnauthorizedError(detail="Session has been invalidated")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError(detail="Actor not found")

    if not user.is_active or user.status not in ("active",):
        raise UnauthorizedError(detail="Actor is not active")

    role = None
    perm_keys: list[str] = []
    if user.role_id:
        role_result = await db.execute(select(RoleModel).where(RoleModel.id == user.role_id))
        role = role_result.scalar_one_or_none()
        if role:
            perm_result = await db.execute(
                select(PermissionModel.key)
                .select_from(RolePermission)
                .join(PermissionModel, RolePermission.permission_id == PermissionModel.id)
                .where(RolePermission.role_id == user.role_id)
            )
            perm_keys = [row[0] for row in perm_result.all()]

    return {
        "id": str(user.id),
        "email": user.email,
        "role": role.slug if role else None,
        "permissions": perm_keys,
        "is_active": user.is_active,
        "user_id": str(user.id),
    }


async def get_optional_current_actor(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Optional[dict]:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        return await get_current_actor(request, db)
    except Exception:
        return None


def require_permission(*permissions: PermissionKey):
    async def _check(
        actor: dict = Depends(get_current_actor),
    ) -> dict:
        actor_perms = set(actor.get("permissions", []))
        for perm in permissions:
            if perm.value not in actor_perms:
                raise ForbiddenError(
                    detail=f"Missing required permission: {perm.value}",
                    error_code="PERMISSION_DENIED",
                )
        return actor

    return _check


def require_role(*roles: str):
    async def _check(
        actor: dict = Depends(get_current_actor),
    ) -> dict:
        actor_role = actor.get("role")
        if actor_role not in roles:
            raise ForbiddenError(
                detail=f"Role '{actor_role}' is not authorized for this action",
                error_code="ROLE_DENIED",
            )
        return actor

    return _check


async def get_tenant_context(
    request: Request,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
) -> TenantContext:
    ctx = await _resolve_tenant_context(request, actor, db)
    await apply_rls_context_from_tenant_context(db, ctx)
    return ctx


async def get_optional_tenant_context(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Optional[TenantContext]:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        actor = await get_current_actor(request, db)
        ctx = await _resolve_tenant_context(request, actor, db)
        await apply_rls_context_from_tenant_context(db, ctx)
        return ctx
    except Exception:
        return None


async def _resolve_tenant_context(
    request: Request,
    actor: dict,
    db: AsyncSession,
) -> TenantContext:
    actor_id = UUID(actor["id"])
    actor_role = actor.get("role")

    membership = None
    tenant_id = None

    result = await db.execute(
        select(AgencyEmployeeMembership).where(
            AgencyEmployeeMembership.user_id == actor_id,
            AgencyEmployeeMembership.status == "active",
        )
    )
    membership = result.scalars().first()

    if membership:
        tenant_id = membership.agency_tenant_id

    return TenantContext(
        actor_id=actor_id,
        role=actor_role,
        permissions=actor.get("permissions", []),
        tenant_id=tenant_id,
        membership_id=membership.id if membership else None,
        is_platform_actor=actor_role == "platform_admin",
        request_id=getattr(request.state, "request_id", None),
        source="api",
    )


async def get_rls_db_session(
    db: AsyncSession = Depends(get_db_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> AsyncSession:
    return db


async def get_optional_rls_db_session(
    db: AsyncSession = Depends(get_db_session),
    ctx: Optional[TenantContext] = Depends(get_optional_tenant_context),
) -> AsyncSession:
    return db
