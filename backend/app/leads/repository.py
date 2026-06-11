from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.leads.models import Lead, ReviewedLeadRecord


class LeadRepository(BaseRepository):
    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Lead], int]:
        count_q = select(func.count(Lead.id)).where(Lead.user_id == user_id)
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(Lead)
            .where(Lead.user_id == user_id)
            .order_by(Lead.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20,
        reviewed: Optional[bool] = None, status: Optional[str] = None,
    ) -> tuple[list[Lead], int]:
        base_where = [Lead.agency_tenant_id == tenant_id]

        if reviewed is True:
            base_where.append(Lead.status == "reviewed")
        elif reviewed is False:
            base_where.append(Lead.status != "reviewed")

        if status is not None:
            base_where.append(Lead.status == status)

        count_q = select(func.count(Lead.id)).where(*base_where)
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(Lead)
            .where(*base_where)
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

    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[ReviewedLeadRecord], int]:
        count_q = select(func.count(ReviewedLeadRecord.id)).where(
            ReviewedLeadRecord.agency_tenant_id == tenant_id
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(ReviewedLeadRecord)
            .where(ReviewedLeadRecord.agency_tenant_id == tenant_id)
            .order_by(ReviewedLeadRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total
