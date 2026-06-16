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

    async def create_manual_search_log(
        self,
        user_id: Optional[UUID],
        filters: dict,
        sort: Optional[str],
        result_count: int,
    ) -> SearchLog:
        log = SearchLog(
            user_id=user_id,
            source_mode="manual",
            event_type="manual_search",
            filters=filters,
            sort=sort,
            result_count=result_count,
        )
        return await self.create(log)

    async def create_ai_text_search_log(
        self,
        user_id: Optional[UUID],
        raw_query_redacted: Optional[str],
        intent: Optional[dict],
        filters: dict,
        result_count: int,
        provider: Optional[str] = None,
        fallback_reason: Optional[str] = None,
    ) -> SearchLog:
        log = SearchLog(
            user_id=user_id,
            source_mode="ai_text",
            event_type="ai_text_search",
            raw_query_redacted=raw_query_redacted,
            intent=intent,
            filters=filters,
            result_count=result_count,
            provider=provider,
            fallback_reason=fallback_reason,
        )
        return await self.create(log)

    async def create_voice_search_log(
        self,
        user_id: Optional[UUID],
        transcript_redacted: Optional[str],
        intent: Optional[dict],
        filters: dict,
        result_count: int,
        provider: Optional[str] = None,
        fallback_reason: Optional[str] = None,
    ) -> SearchLog:
        log = SearchLog(
            user_id=user_id,
            source_mode="voice",
            event_type="voice_search",
            transcript_redacted=transcript_redacted,
            intent=intent,
            filters=filters,
            result_count=result_count,
            provider=provider,
            fallback_reason=fallback_reason,
        )
        return await self.create(log)

    async def create_confirmation_log(
        self,
        user_id: Optional[UUID],
        source_mode: str,
        filters: dict,
        edits: Optional[list] = None,
    ) -> SearchLog:
        log = SearchLog(
            user_id=user_id,
            source_mode=source_mode,
            event_type="search_confirmation",
            filters=filters,
            intent={"edits": edits} if edits else None,
            result_count=0,
        )
        return await self.create(log)


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
