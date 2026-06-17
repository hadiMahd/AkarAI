from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.leads.models import Lead, LeadSpamResult, LeadLevelResult, ReviewedLeadRecord


class LeadProcessingQueryService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_spam_result_by_lead(self, lead_id: UUID) -> LeadSpamResult | None:
        stmt = select(LeadSpamResult).where(LeadSpamResult.lead_id == lead_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_level_result_by_lead(self, lead_id: UUID) -> LeadLevelResult | None:
        stmt = select(LeadLevelResult).where(LeadLevelResult.lead_id == lead_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_spam_result_by_idempotency(
        self, lead_id: UUID, idempotency_key: str
    ) -> LeadSpamResult | None:
        stmt = select(LeadSpamResult).where(
            LeadSpamResult.lead_id == lead_id,
            LeadSpamResult.idempotency_key == idempotency_key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_level_result_by_idempotency(
        self, lead_id: UUID, idempotency_key: str
    ) -> LeadLevelResult | None:
        stmt = select(LeadLevelResult).where(
            LeadLevelResult.lead_id == lead_id,
            LeadLevelResult.idempotency_key == idempotency_key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_lead_processing_summary(self, tenant_id: UUID) -> dict:
        spam_counts = (
            select(
                func.count(LeadSpamResult.id).label("total_spam"),
                func.count().filter(LeadSpamResult.label == "spam").label("spam"),
                func.count().filter(LeadSpamResult.label == "not_spam").label("not_spam"),
                func.count().filter(LeadSpamResult.status == "pending").label("spam_pending"),
                func.count().filter(LeadSpamResult.status == "failed").label("spam_failed"),
            )
            .where(
                LeadSpamResult.agency_tenant_id == tenant_id,
            )
        )
        spam_row = (await self._session.execute(spam_counts)).one()

        level_counts = (
            select(
                func.count(LeadLevelResult.id).label("total_level"),
                func.count().filter(LeadLevelResult.level == "hot").label("hot"),
                func.count().filter(LeadLevelResult.level == "normal").label("normal"),
                func.count().filter(LeadLevelResult.status == "pending").label("level_pending"),
                func.count().filter(LeadLevelResult.status == "failed").label("level_failed"),
            )
            .where(
                LeadLevelResult.agency_tenant_id == tenant_id,
            )
        )
        level_row = (await self._session.execute(level_counts)).one()

        review_count = (
            select(func.count(ReviewedLeadRecord.id))
            .where(ReviewedLeadRecord.agency_tenant_id == tenant_id)
        )
        total_reviewed = (await self._session.execute(review_count)).scalar() or 0

        total_leads = (
            select(func.count(Lead.id))
            .where(Lead.agency_tenant_id == tenant_id)
        )
        total = (await self._session.execute(total_leads)).scalar() or 0

        pending = (
            select(func.count(Lead.id))
            .where(
                Lead.agency_tenant_id == tenant_id,
                Lead.processing_status == "pending",
            )
        )
        pending_count = (await self._session.execute(pending)).scalar() or 0

        return {
            "total_leads": total,
            "spam_count": spam_row.spam or 0,
            "not_spam_count": spam_row.not_spam or 0,
            "hot_count": level_row.hot or 0,
            "normal_count": level_row.normal or 0,
            "pending_count": pending_count,
            "reviewed_count": total_reviewed,
            "fallback_count": (spam_row.spam_failed or 0) + (level_row.level_failed or 0),
        }

    async def get_trend_summary(self, tenant_id: UUID) -> dict:
        summary = await self.get_lead_processing_summary(tenant_id)
        total = summary["total_leads"] or 1
        not_spam = summary["not_spam_count"]
        hot = summary["hot_count"]
        reviewed = summary["reviewed_count"]
        return {
            **summary,
            "spam_rate": round(summary["spam_count"] / total, 4) if total > 0 else 0.0,
            "hot_rate": round(hot / max(not_spam, 1), 4) if not_spam > 0 else 0.0,
            "review_rate": round(reviewed / total, 4) if total > 0 else 0.0,
            "fallback_count": summary["fallback_count"],
        }
