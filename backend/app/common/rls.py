import contextvars
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_rls_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "rls_tenant_id", default=None
)
_rls_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "rls_user_id", default=None
)
_rls_role: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "rls_role", default=None
)
_rls_is_platform_admin: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "rls_is_platform_admin", default=False
)

SET_CONFIG_SQL = text(
    "SELECT set_config(:key, :value, true)"
)
CLEAR_CONFIG_SQL = text(
    "SELECT set_config(:key, '', true)"
)


def set_rls_context_vars(
    *,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    role: Optional[str] = None,
    is_platform_admin: bool = False,
) -> None:
    _rls_tenant_id.set(str(tenant_id) if tenant_id else None)
    _rls_user_id.set(str(user_id) if user_id else None)
    _rls_role.set(role)
    _rls_is_platform_admin.set(is_platform_admin)


def clear_rls_context_vars() -> None:
    _rls_tenant_id.set(None)
    _rls_user_id.set(None)
    _rls_role.set(None)
    _rls_is_platform_admin.set(False)


def get_rls_context_values() -> dict:
    return {
        "tenant_id": _rls_tenant_id.get(),
        "user_id": _rls_user_id.get(),
        "role": _rls_role.get(),
        "is_platform_admin": _rls_is_platform_admin.get(),
    }


def has_rls_context() -> bool:
    return bool(
        _rls_tenant_id.get()
        or _rls_user_id.get()
        or _rls_is_platform_admin.get()
    )


async def apply_rls_context_to_session(
    session: AsyncSession,
    *,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    role: Optional[str] = None,
    is_platform_admin: bool = False,
) -> None:
    tid = str(tenant_id) if tenant_id else ""
    uid = str(user_id) if user_id else ""
    await session.execute(SET_CONFIG_SQL, {"key": "app.tenant_id", "value": tid})
    await session.execute(SET_CONFIG_SQL, {"key": "app.user_id", "value": uid})
    await session.execute(
        SET_CONFIG_SQL,
        {"key": "app.role", "value": role or ""},
    )
    await session.execute(
        SET_CONFIG_SQL,
        {"key": "app.is_platform_admin", "value": "true" if is_platform_admin else "false"},
    )


async def clear_rls_context_on_session(session: AsyncSession) -> None:
    for key in ("app.tenant_id", "app.user_id", "app.role", "app.is_platform_admin"):
        await session.execute(CLEAR_CONFIG_SQL, {"key": key})


async def apply_rls_context_from_tenant_context(
    session: AsyncSession,
    ctx,
) -> None:
    if ctx is None:
        return
    await apply_rls_context_to_session(
        session,
        tenant_id=ctx.tenant_id,
        user_id=ctx.actor_id,
        role=ctx.role,
        is_platform_admin=ctx.is_platform_actor,
    )
