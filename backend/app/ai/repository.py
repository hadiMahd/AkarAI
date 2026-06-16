"""Repository for agency AI job, lead reply draft, comparison summary,
and tool invocation records.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models import (
    AgencyAIJob,
    AgencyAssistantToolInvocation,
    ComparisonSummary,
    LeadReplyDraft,
)


class AgencyAIRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(self, job: AgencyAIJob) -> AgencyAIJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job(
        self,
        job_id: UUID,
        *,
        tenant_id: UUID | None = None,
    ) -> AgencyAIJob | None:
        stmt = select(AgencyAIJob).where(AgencyAIJob.id == job_id)
        if tenant_id is not None:
            stmt = stmt.where(AgencyAIJob.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_job(self, job: AgencyAIJob) -> AgencyAIJob:
        await self.session.flush()
        return job

    async def create_lead_reply_draft(self, draft: LeadReplyDraft) -> LeadReplyDraft:
        self.session.add(draft)
        await self.session.flush()
        return draft

    async def list_lead_reply_drafts(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        limit: int = 5,
    ) -> list[LeadReplyDraft]:
        stmt = (
            select(LeadReplyDraft)
            .where(
                LeadReplyDraft.lead_id == lead_id,
                LeadReplyDraft.agency_tenant_id == tenant_id,
            )
            .order_by(LeadReplyDraft.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_comparison_summary(
        self,
        summary: ComparisonSummary,
    ) -> ComparisonSummary:
        self.session.add(summary)
        await self.session.flush()
        return summary

    async def list_comparison_summaries_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 5,
    ) -> list[ComparisonSummary]:
        stmt = (
            select(ComparisonSummary)
            .where(ComparisonSummary.user_id == user_id)
            .order_by(ComparisonSummary.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_tool_invocation(
        self,
        invocation: AgencyAssistantToolInvocation,
    ) -> AgencyAssistantToolInvocation:
        self.session.add(invocation)
        await self.session.flush()
        return invocation

    async def list_tool_invocations_for_tenant(
        self,
        tenant_id: UUID,
        *,
        limit: int = 50,
    ) -> list[AgencyAssistantToolInvocation]:
        stmt = (
            select(AgencyAssistantToolInvocation)
            .where(AgencyAssistantToolInvocation.tenant_id == tenant_id)
            .order_by(AgencyAssistantToolInvocation.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
