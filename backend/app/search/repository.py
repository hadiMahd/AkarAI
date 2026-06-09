from typing import Optional
from uuid import UUID

from sqlalchemy import select, func

from app.common.repository import BaseRepository
from app.search.models import SearchLog
from app.common.events import DomainEventLog


class SearchLogRepository(BaseRepository):
    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[SearchLog], int]:
        count_q = select(func.count(SearchLog.id)).where(SearchLog.agency_tenant_id == tenant_id)
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(SearchLog)
            .where(SearchLog.agency_tenant_id == tenant_id)
            .order_by(SearchLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def create(self, log: SearchLog) -> SearchLog:
        self.session.add(log)
        await self.session.flush()
        return log


class DomainLogRepository(BaseRepository):
    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[DomainEventLog], int]:
        count_q = select(func.count(DomainEventLog.id)).where(
            DomainEventLog.agency_tenant_id == tenant_id
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(DomainEventLog)
            .where(DomainEventLog.agency_tenant_id == tenant_id)
            .order_by(DomainEventLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total
