from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError, ForbiddenError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.tenant import TenantContext, require_tenant
from app.search.repository import SearchLogRepository, DomainLogRepository
from app.search.models import SearchLog


class SearchService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._search_repo = SearchLogRepository(session, tenant)
        self._domain_repo = DomainLogRepository(session, tenant)

    async def log_search_event(self, data: dict) -> SearchLog:
        log = SearchLog(
            user_id=data.get("user_id"),
            agency_tenant_id=data.get("agency_tenant_id"),
            filters=data.get("filters"),
            sort=data.get("sort"),
            result_count=data.get("result_count", 0),
        )
        return await self._search_repo.create(log)

    async def list_search_logs(self, pagination: PaginationRequest) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._search_repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def list_domain_logs(self, pagination: PaginationRequest) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._domain_repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)
