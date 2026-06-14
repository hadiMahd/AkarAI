from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.exceptions import NotFoundError
from app.common.pagination import PaginationRequest
from app.rag.models import (
    RagChatMessage,
    RagChatThread,
    RagChunk,
    RagDocument,
    RagEvaluationExample,
    RagEvaluationRun,
    RagPage,
    RagRetrievalLog,
)
from app.rag.schemas import RagRetrievalLogFilter


class RagRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_document(self, document: RagDocument) -> RagDocument:
        self._session.add(document)
        await self._session.flush()
        return document

    async def get_document(self, document_id: UUID, tenant_id: UUID) -> RagDocument | None:
        result = await self._session.execute(
            select(RagDocument).where(
                RagDocument.id == document_id,
                RagDocument.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_document(self, document: RagDocument) -> RagDocument:
        await self._session.flush()
        return document

    async def list_documents(self, tenant_id: UUID, pagination: PaginationRequest) -> tuple[list[RagDocument], int]:
        base = select(RagDocument).where(RagDocument.tenant_id == tenant_id)
        count_result = await self._session.execute(select(func.count()).select_from(base.subquery()))
        total = int(count_result.scalar_one())
        result = await self._session.execute(
            base.order_by(RagDocument.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(result.scalars().all()), total

    async def get_document_for_worker(self, document_id: UUID) -> RagDocument | None:
        result = await self._session.execute(select(RagDocument).where(RagDocument.id == document_id))
        return result.scalar_one_or_none()

    async def list_pages_for_document(self, document_id: UUID) -> list[RagPage]:
        result = await self._session.execute(
            select(RagPage).where(RagPage.document_id == document_id).order_by(RagPage.page_number)
        )
        return list(result.scalars().all())

    async def create_pages(self, pages: list[RagPage]) -> list[RagPage]:
        self._session.add_all(pages)
        await self._session.flush()
        return pages

    async def delete_chunks_for_document(self, document_id: UUID) -> None:
        await self._session.execute(delete(RagChunk).where(RagChunk.document_id == document_id))

    async def create_chunks(self, chunks: list[RagChunk]) -> list[RagChunk]:
        self._session.add_all(chunks)
        await self._session.flush()
        return chunks

    async def get_chunk_by_hash(self, tenant_id: UUID, document_id: UUID, content_hash: str) -> RagChunk | None:
        result = await self._session.execute(
            select(RagChunk).where(
                RagChunk.tenant_id == tenant_id,
                RagChunk.document_id == document_id,
                RagChunk.content_hash == content_hash,
            )
        )
        return result.scalar_one_or_none()

    async def orphan_unused_chunks(self, document_id: UUID, active_hashes: set[str]) -> int:
        result = await self._session.execute(
            delete(RagChunk)
            .where(RagChunk.document_id == document_id, RagChunk.content_hash.not_in(active_hashes))
            .returning(RagChunk.id)
        )
        return len(list(result.all()))

    async def list_processed_documents(self, tenant_id: UUID) -> list[RagDocument]:
        result = await self._session.execute(
            select(RagDocument).where(
                RagDocument.tenant_id == tenant_id,
                RagDocument.status == "processed",
            )
        )
        return list(result.scalars().all())

    async def list_active_chunks(self, tenant_id: UUID, document_ids: list[UUID] | None = None) -> list[RagChunk]:
        query = select(RagChunk).where(RagChunk.tenant_id == tenant_id, RagChunk.status == "active")
        if document_ids:
            query = query.where(RagChunk.document_id.in_(document_ids))
        result = await self._session.execute(query.order_by(RagChunk.created_at.desc()))
        return list(result.scalars().all())

    async def list_parent_pages(self, tenant_id: UUID, page_ids: list[UUID]) -> list[RagPage]:
        if not page_ids:
            return []
        result = await self._session.execute(
            select(RagPage).where(
                RagPage.tenant_id == tenant_id,
                RagPage.id.in_(page_ids),
            )
        )
        return list(result.scalars().all())

    async def create_retrieval_log(self, log: RagRetrievalLog) -> RagRetrievalLog:
        self._session.add(log)
        await self._session.flush()
        return log

    async def list_retrieval_logs(
        self,
        tenant_id: UUID,
        pagination: PaginationRequest,
        filters: RagRetrievalLogFilter | None = None,
    ) -> tuple[list[RagRetrievalLog], int]:
        base = select(RagRetrievalLog).where(RagRetrievalLog.tenant_id == tenant_id)
        if filters:
            if filters.actor_role:
                base = base.where(RagRetrievalLog.actor_role == filters.actor_role)
            if filters.confidence_status:
                base = base.where(RagRetrievalLog.confidence_status == filters.confidence_status)
            if filters.date_from:
                base = base.where(RagRetrievalLog.created_at >= filters.date_from)
            if filters.date_to:
                base = base.where(RagRetrievalLog.created_at <= filters.date_to)
        count_result = await self._session.execute(select(func.count()).select_from(base.subquery()))
        total = int(count_result.scalar_one())
        result = await self._session.execute(
            base.order_by(RagRetrievalLog.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(result.scalars().all()), total

    async def create_evaluation_run(self, run: RagEvaluationRun) -> RagEvaluationRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def create_evaluation_examples(self, examples: list[RagEvaluationExample]) -> list[RagEvaluationExample]:
        if not examples:
            return []
        self._session.add_all(examples)
        await self._session.flush()
        return examples

    async def list_evaluation_runs(
        self,
        tenant_id: UUID | None,
        pagination: PaginationRequest,
    ) -> tuple[list[RagEvaluationRun], int]:
        base = select(RagEvaluationRun).order_by(RagEvaluationRun.created_at.desc())
        count_result = await self._session.execute(select(func.count()).select_from(base.subquery()))
        total = int(count_result.scalar_one())
        result = await self._session.execute(
            base.offset(pagination.offset).limit(pagination.limit)
        )
        return list(result.scalars().all()), total

    async def search_chunks_by_embedding(
        self,
        tenant_id: UUID,
        query_embedding: list[float],
        top_k: int = 8,
    ) -> list[tuple[RagChunk, RagDocument, float]]:
        distance = RagChunk.embedding.cosine_distance(query_embedding)
        result = await self._session.execute(
            select(RagChunk, RagDocument, distance.label("distance"))
            .join(RagDocument, RagChunk.document_id == RagDocument.id)
            .where(
                RagChunk.tenant_id == tenant_id,
                RagChunk.status == "active",
                RagDocument.tenant_id == tenant_id,
                RagDocument.status == "processed",
                RagChunk.embedding.isnot(None),
            )
            .order_by(distance)
            .limit(top_k)
        )
        rows = result.all()
        return [(r[0], r[1], float(r[2])) for r in rows]

    async def get_chunks_by_ids(
        self, tenant_id: UUID, chunk_ids: list[UUID]
    ) -> list[RagChunk]:
        if not chunk_ids:
            return []
        result = await self._session.execute(
            select(RagChunk).where(
                RagChunk.tenant_id == tenant_id,
                RagChunk.id.in_(chunk_ids),
            )
        )
        return list(result.scalars().all())

    async def get_documents_by_ids(
        self, tenant_id: UUID, document_ids: list[UUID]
    ) -> list[RagDocument]:
        if not document_ids:
            return []
        result = await self._session.execute(
            select(RagDocument).where(
                RagDocument.tenant_id == tenant_id,
                RagDocument.id.in_(document_ids),
            )
        )
        return list(result.scalars().all())

    async def create_chat_thread(self, thread: RagChatThread) -> RagChatThread:
        self._session.add(thread)
        await self._session.flush()
        return thread

    async def get_chat_thread(
        self, thread_id: UUID, tenant_id: UUID, owner_user_id: UUID
    ) -> RagChatThread | None:
        result = await self._session.execute(
            select(RagChatThread).where(
                RagChatThread.id == thread_id,
                RagChatThread.tenant_id == tenant_id,
                RagChatThread.owner_user_id == owner_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_chat_threads(
        self,
        tenant_id: UUID,
        owner_user_id: UUID,
        pagination: PaginationRequest,
    ) -> tuple[list[tuple[RagChatThread, int]], int]:
        message_count_subq = (
            select(
                RagChatMessage.thread_id.label("thread_id"),
                func.count(RagChatMessage.id).label("message_count"),
            )
            .group_by(RagChatMessage.thread_id)
            .subquery()
        )
        base = (
            select(
                RagChatThread,
                func.coalesce(message_count_subq.c.message_count, 0).label("message_count"),
            )
            .outerjoin(message_count_subq, message_count_subq.c.thread_id == RagChatThread.id)
            .where(
                RagChatThread.tenant_id == tenant_id,
                RagChatThread.owner_user_id == owner_user_id,
            )
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(count_result.scalar_one())
        result = await self._session.execute(
            base.order_by(RagChatThread.last_message_at.desc(), RagChatThread.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        rows = []
        for thread, message_count in result.all():
            rows.append((thread, int(message_count or 0)))
        return rows, total

    async def update_chat_thread(self, thread: RagChatThread) -> RagChatThread:
        await self._session.flush()
        return thread

    async def list_chat_messages(
        self, thread_id: UUID, tenant_id: UUID, owner_user_id: UUID
    ) -> list[RagChatMessage]:
        result = await self._session.execute(
            select(RagChatMessage)
            .where(
                RagChatMessage.thread_id == thread_id,
                RagChatMessage.tenant_id == tenant_id,
                RagChatMessage.owner_user_id == owner_user_id,
            )
            .order_by(RagChatMessage.sequence_number.asc(), RagChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_next_chat_sequence_number(self, thread_id: UUID) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(RagChatMessage.sequence_number), 0))
            .where(RagChatMessage.thread_id == thread_id)
        )
        current = int(result.scalar_one())
        return current + 1

    async def create_chat_message(self, message: RagChatMessage) -> RagChatMessage:
        self._session.add(message)
        await self._session.flush()
        return message
