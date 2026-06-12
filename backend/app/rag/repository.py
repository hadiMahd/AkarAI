from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.pagination import PaginationRequest
from app.rag.models import RagChunk, RagDocument, RagPage


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
