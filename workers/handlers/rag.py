from __future__ import annotations

import hashlib
import logging
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.registry import get_embedding_provider
from app.common.config import settings
from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session
from app.common.storage import delete_object, download_object, get_rag_bucket, upload_object
import app.agencies.models  # noqa: F401 - load agency_tenants metadata for RAG FKs
from app.rag.models import RagChunk, RagDocument, RagPage

logger = logging.getLogger("worker.rag")
RAG_WORKER_ACTOR_ID = uuid5(NAMESPACE_DNS, "akarai-rag-worker")


async def handle_rag_document_uploaded(payload: dict) -> None:
    document_id = payload.get("document_id")
    tenant_id = payload.get("tenant_id")
    blob_path = payload.get("blob_path")

    if not all([document_id, tenant_id, blob_path]):
        logger.error("Missing required fields in payload: %s", payload)
        raise ValueError("Missing required fields in RAG upload payload")

    document_uuid = UUID(document_id)
    tenant_uuid = UUID(tenant_id)
    logger.info("Processing RAG document %s", document_id)

    async with async_session_factory() as session:
        page_blob_paths: list[str] = []

        async def apply_worker_rls_context() -> None:
            await apply_rls_context_to_session(
                session,
                tenant_id=tenant_uuid,
                user_id=RAG_WORKER_ACTOR_ID,
                role="rag_worker",
                is_platform_admin=False,
            )

        await apply_worker_rls_context()

        try:
            result = await session.execute(
                select(RagDocument).where(RagDocument.id == document_uuid)
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.error("Document %s not found", document_id)
                raise ValueError(f"Document {document_id} not found")

            document.status = "processing"
            await session.commit()
            await apply_worker_rls_context()

            bucket = get_rag_bucket()
            pdf_bytes = download_object(bucket, blob_path)

            pages_data = extract_text_from_pdf(pdf_bytes)

            if not pages_data:
                document.status = "failed"
                await session.commit()
                logger.warning("No text extracted from document %s", document_id)
                return

            # Build new-page objects in memory (NOT added to session yet).
            # IDs are generated client-side by uuid4 so they are available
            # without a flush.
            new_pages: list[RagPage] = []
            for page_num, page_text in enumerate(pages_data, start=1):
                page_blob_path = (
                    f"rag-vault/{tenant_id}/{document_id}/pages/page_{page_num}.txt"
                )
                upload_object(
                    bucket, page_blob_path, page_text.encode("utf-8"), "text/plain"
                )
                page_blob_paths.append(page_blob_path)
                page = RagPage(
                    id=uuid4(),
                    document_id=document_uuid,
                    tenant_id=tenant_uuid,
                    page_number=page_num,
                    blob_path=page_blob_path,
                    content=page_text,
                )
                new_pages.append(page)

            chunks_data = create_chunks_from_pages(new_pages)

            if not chunks_data:
                _cleanup_page_blobs(bucket, page_blob_paths)
                document.status = "failed"
                await session.commit()
                logger.warning("No chunks created from document %s", document_id)
                return

            # Build lookup: content_hash → chunk data (with new page_ids)
            chunks_by_hash: dict[str, dict] = {}
            for chunk_data in chunks_data:
                h = chunk_data["content_hash"]
                if h in chunks_by_hash:
                    chunks_by_hash[h]["page_ids"].extend(chunk_data["page_ids"])
                else:
                    chunks_by_hash[h] = {
                        "text": chunk_data["text"],
                        "page_ids": list(chunk_data["page_ids"]),
                        "content_hash": h,
                    }
            active_hashes = set(chunks_by_hash.keys())

            # Load existing chunks
            existing_chunks = await session.execute(
                select(RagChunk).where(RagChunk.document_id == document_uuid)
            )
            existing_by_hash: dict[str, RagChunk] = {}
            for chunk in existing_chunks.scalars().all():
                existing_by_hash[chunk.content_hash] = chunk

            new_hashes: list[str] = []
            for h in active_hashes:
                if h not in existing_by_hash:
                    new_hashes.append(h)

            # Generate embeddings for new chunks ONLY.
            # If this fails we never modified pages in the DB, so the
            # document stays in its last-committed state ("processing").
            embeddings = None
            if new_hashes:
                try:
                    embedding_provider = get_embedding_provider()
                    texts_to_embed = [chunks_by_hash[h]["text"] for h in new_hashes]
                    embeddings = await embedding_provider.embed(texts_to_embed)
                except Exception as e:
                    logger.error(
                        "Failed to generate embeddings for document %s: %s",
                        document_id,
                        e,
                    )
                    _cleanup_page_blobs(bucket, page_blob_paths)
                    document.status = "failed"
                    await session.commit()
                    return

            # === SUCCESS PATH ===
            # Only now do we modify pages/chunks in the database.

            # Delete old pages
            old_pages = await session.execute(
                select(RagPage).where(RagPage.document_id == document_uuid)
            )
            for page in old_pages.scalars().all():
                await session.delete(page)
            await session.flush()

            # Insert new pages
            for page in new_pages:
                session.add(page)
            await session.flush()

            # Remap page_ids on reused chunks and mark them active
            reused_count = 0
            for h in active_hashes:
                existing = existing_by_hash.get(h)
                if existing is not None:
                    existing.page_ids = chunks_by_hash[h]["page_ids"]
                    existing.status = "active"
                    reused_count += 1

            # Insert new chunks with embeddings
            if new_hashes and embeddings:
                for i, h in enumerate(new_hashes):
                    chunk_data = chunks_by_hash[h]
                    chunk = RagChunk(
                        document_id=document_uuid,
                        tenant_id=tenant_uuid,
                        page_ids=chunk_data["page_ids"],
                        content_hash=h,
                        text=chunk_data["text"],
                        embedding=embeddings[i],
                        status="active",
                    )
                    session.add(chunk)

                await session.flush()

            orphaned_count = await orphan_chunks_not_in_set(
                session, document_uuid, active_hashes
            )

            document.status = "processed"
            await session.commit()

            logger.info(
                "Processed document %s: %d pages, %d chunks "
                "(%d new, %d reused, %d orphaned)",
                document_id,
                len(new_pages),
                len(chunks_by_hash),
                len(new_hashes),
                reused_count,
                orphaned_count,
            )

        except Exception as e:
            logger.exception(
                "Failed to process RAG document %s: %s", document_id, e
            )
            _cleanup_page_blobs(get_rag_bucket(), page_blob_paths)
            await session.rollback()
            try:
                await apply_worker_rls_context()
                result = await session.execute(
                    select(RagDocument).where(RagDocument.id == document_uuid)
                )
                document = result.scalar_one_or_none()
                if document:
                    document.status = "failed"
                    await session.commit()
            except Exception:
                pass
            raise


async def orphan_chunks_not_in_set(
    session: AsyncSession, document_id: UUID, active_hashes: set[str]
) -> int:
    result = await session.execute(
        select(RagChunk).where(
            RagChunk.document_id == document_id,
            RagChunk.content_hash.notin_(active_hashes),
            RagChunk.status == "active",
        )
    )
    chunks = list(result.scalars().all())
    for chunk in chunks:
        chunk.status = "orphaned"
    await session.flush()
    return len(chunks)


def extract_text_from_pdf(pdf_bytes: bytes) -> list[str]:
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF not installed")
        raise

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []

    try:
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages_text.append(text)
    finally:
        doc.close()

    return pages_text


def create_chunks_from_pages(pages: list[RagPage]) -> list[dict]:
    try:
        import fastcdc
    except ImportError:
        logger.error("fastcdc not installed")
        raise

    chunks_data = []

    for page in pages:
        if not page.content.strip():
            continue

        content_bytes = page.content.encode("utf-8")
        chunker = fastcdc.fastcdc(
            content_bytes,
            min_size=settings.rag_fastcdc_min_size,
            avg_size=settings.rag_fastcdc_avg_size,
            max_size=settings.rag_fastcdc_max_size,
            fat=settings.rag_fastcdc_fat,
        )

        for chunk in chunker:
            chunk_text = chunk.data.decode("utf-8", errors="ignore")

            if not chunk_text.strip():
                continue

            content_hash = hashlib.sha256(
                chunk_text.encode("utf-8")
            ).hexdigest()

            chunks_data.append(
                {
                    "text": chunk_text,
                    "page_ids": [page.id],
                    "content_hash": content_hash,
                }
            )

    return chunks_data


def _cleanup_page_blobs(bucket: str, blob_paths: list[str]) -> None:
    for blob_path in blob_paths:
        try:
            delete_object(bucket, blob_path)
        except Exception:
            logger.warning("Failed to clean up page blob %s", blob_path)
