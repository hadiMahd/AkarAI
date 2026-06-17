from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.leads.models import Lead, ReviewedLeadRecord, LeadSpamResult, LeadLevelResult


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
        spam_label: Optional[str] = None, processing_status: Optional[str] = None,
    ) -> tuple[list[Lead], int]:
        base_where = [Lead.agency_tenant_id == tenant_id]

        if reviewed is True:
            base_where.append(Lead.status == "reviewed")
        elif reviewed is False:
            base_where.append(Lead.status != "reviewed")

        if status is not None:
            base_where.append(Lead.status == status)

        if processing_status is not None:
            base_where.append(Lead.processing_status == processing_status)

        if spam_label is not None:
            subq = select(LeadSpamResult.lead_id).where(
                LeadSpamResult.agency_tenant_id == tenant_id,
                LeadSpamResult.label == spam_label,
            )
            base_where.append(Lead.id.in_(subq))

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

    async def update_processing_status(self, lead_id: UUID, processing_status: str) -> None:
        lead = await self.get_by_id(lead_id)
        if lead is not None:
            lead.processing_status = processing_status
            await self.session.flush()


class LeadSpamResultRepository(BaseRepository):
    async def create_pending(self, lead_id: UUID, tenant_id: UUID) -> LeadSpamResult:
        result = LeadSpamResult(
            lead_id=lead_id,
            agency_tenant_id=tenant_id,
            status="pending",
        )
        self.session.add(result)
        await self.session.flush()
        return result

    async def upsert_result(
        self,
        lead_id: UUID,
        tenant_id: UUID,
        *,
        status: str,
        label: str | None = None,
        score: float | None = None,
        details: dict | None = None,
        retry_count: int = 0,
        last_error: str | None = None,
        idempotency_key: str | None = None,
    ) -> LeadSpamResult:
        existing = await self.session.execute(
            select(LeadSpamResult).where(LeadSpamResult.lead_id == lead_id)
        )
        result = existing.scalar_one_or_none()

        if result is None:
            result = LeadSpamResult(
                lead_id=lead_id,
                agency_tenant_id=tenant_id,
                status=status,
                label=label,
                score=score,
                details=details,
                retry_count=retry_count,
                last_error=last_error,
                idempotency_key=idempotency_key,
            )
            self.session.add(result)
        else:
            result.status = status
            if label is not None:
                result.label = label
            if score is not None:
                result.score = score
            if details is not None:
                result.details = details
            result.retry_count = retry_count
            if last_error is not None:
                result.last_error = last_error
            if idempotency_key is not None:
                result.idempotency_key = idempotency_key

        await self.session.flush()
        return result

    async def get_by_lead(self, lead_id: UUID) -> Optional[LeadSpamResult]:
        result = await self.session.execute(
            select(LeadSpamResult).where(LeadSpamResult.lead_id == lead_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency(self, lead_id: UUID, idempotency_key: str) -> Optional[LeadSpamResult]:
        result = await self.session.execute(
            select(LeadSpamResult).where(
                LeadSpamResult.lead_id == lead_id,
                LeadSpamResult.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()


class LeadLevelResultRepository(BaseRepository):
    async def create_pending(self, lead_id: UUID, tenant_id: UUID) -> LeadLevelResult:
        result = LeadLevelResult(
            lead_id=lead_id,
            agency_tenant_id=tenant_id,
            status="pending",
        )
        self.session.add(result)
        await self.session.flush()
        return result

    async def upsert_result(
        self,
        lead_id: UUID,
        tenant_id: UUID,
        *,
        status: str,
        level: str | None = None,
        score: float | None = None,
        details: dict | None = None,
        retry_count: int = 0,
        last_error: str | None = None,
        idempotency_key: str | None = None,
    ) -> LeadLevelResult:
        existing = await self.session.execute(
            select(LeadLevelResult).where(LeadLevelResult.lead_id == lead_id)
        )
        result = existing.scalar_one_or_none()

        if result is None:
            result = LeadLevelResult(
                lead_id=lead_id,
                agency_tenant_id=tenant_id,
                status=status,
                level=level,
                score=score,
                details=details,
                retry_count=retry_count,
                last_error=last_error,
                idempotency_key=idempotency_key,
            )
            self.session.add(result)
        else:
            result.status = status
            if level is not None:
                result.level = level
            if score is not None:
                result.score = score
            if details is not None:
                result.details = details
            result.retry_count = retry_count
            if last_error is not None:
                result.last_error = last_error
            if idempotency_key is not None:
                result.idempotency_key = idempotency_key

        await self.session.flush()
        return result

    async def get_by_lead(self, lead_id: UUID) -> Optional[LeadLevelResult]:
        result = await self.session.execute(
            select(LeadLevelResult).where(LeadLevelResult.lead_id == lead_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency(self, lead_id: UUID, idempotency_key: str) -> Optional[LeadLevelResult]:
        result = await self.session.execute(
            select(LeadLevelResult).where(
                LeadLevelResult.lead_id == lead_id,
                LeadLevelResult.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()


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
