from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


# Conventions for Phase 2 dependency injection:
#
# 1. All shared dependencies live in this module or feature-specific
#    `dependencies.py` (e.g. `backend/app/auth/dependencies.py`).
#
# 2. Use `fastapi.Depends` in router signatures. Example:
#       @router.get("/items")
#       async def list_items(
#           db: AsyncSession = Depends(get_db_session),
#           current_user: User = Depends(get_current_user),
#       ):
#
# 3. Transaction boundary: services receive a session, not a dependency
#    callable. Repositories receive the session from their service.
#
# 4. Tenant context: when tenant-aware features land, a `get_tenant_context`
#    dependency will inject `TenantContext` from request state.
#
# 5. Permission checks: a `require_permission(permission)` dependency factory
#    will guard protected endpoints.
#
# 6. Rate limiting: a `rate_limit(key_factory)` dependency factory will
#    enforce per-endpoint throttling.
