from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.leads.models import Lead, ReviewedLeadRecord


class LeadRepository(BaseRepository):
    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Lead], int]:
        count_q = select(func.count(Lead.id)).where(Lead.agency_tenant_id == tenant_id)
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(Lead)
            .where(Lead.agency_tenant_id == tenant_id)
            .order_by(Lead.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_by_id(self, lead_id: UUID) -> Optional[Lead]:
        result = await self.session.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    async def create(self, lead: Lead) -> Lead:
        self.session.add(lead)
        await self.session.flush()
        return lead


class ReviewedLeadRepository(BaseRepository):
    async def create(self, record: ReviewedLeadRecord) -> ReviewedLeadRecord:
        self.session.add(record)
        await self.session.flush()
        return record
