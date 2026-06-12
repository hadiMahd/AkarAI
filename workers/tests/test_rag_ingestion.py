"""Integration tests for RAG document ingestion worker handler.

Tests the core chunking, DB persistence, re-ingestion dedup, and
orphan cleanup logic while mocking MinIO, PyMuPDF, FastCDC, and
the embedding provider to avoid runtime-image dependencies.
"""
import hashlib
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

import pytest

# Add backend to sys.path so we can import app.* (mirrors workers/main.py).
_backend_root = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if os.path.isdir(_backend_root):
    sys.path.insert(0, os.path.abspath(_backend_root))

os.environ.setdefault("APP_ENV", "testing")

from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session
from app.agencies.models import AgencyTenant
from app.rag.models import RagChunk, RagDocument, RagPage


@pytest.fixture
async def db_session():
    async with async_session_factory() as session:
        _orig_commit = session.commit

        async def _commit():
            if session.in_transaction() and not session.is_active:
                await session.rollback()
            await _orig_commit()
            await apply_rls_context_to_session(
                session, role="platform_admin", is_platform_admin=True,
            )

        session.commit = _commit
        await apply_rls_context_to_session(
            session, role="platform_admin", is_platform_admin=True,
        )
        yield session
        await session.rollback()


@pytest.fixture
async def pending_document(db_session):
    """Insert a RagDocument in pending status for the worker to consume."""
    tenant = AgencyTenant(
        id=uuid4(),
        name="Worker Test Tenant",
        slug=f"worker-test-{uuid4().hex[:8]}",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(tenant)
    await db_session.commit()

    doc = RagDocument(
        tenant_id=tenant.id,
        filename="test_policy.pdf",
        status="pending",
        blob_path=f"rag-vault/{uuid4()}/test.pdf",
    )
    db_session.add(doc)
    await db_session.commit()
    yield doc
    await db_session.delete(doc)
    await db_session.delete(tenant)
    await db_session.commit()


FAKE_EMBEDDING = [0.1] * 1536


def _mock_create_chunks(pages: list[RagPage]) -> list[dict]:
    """Deterministic chunk generation that mirrors fastcdc logic but
    produces one chunk per page using the page content hash. This avoids
    the fastcdc runtime dependency while exercising the handler's hash-
    comparison and orphan logic."""
    chunks = []
    for page in pages:
        text = page.content or ""
        if not text.strip():
            continue
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        chunks.append({
            "text": text,
            "page_ids": [page.id],
            "content_hash": h,
        })
    return chunks


@pytest.mark.asyncio
class TestRagIngestion:
    """T015, T016, T017: Worker RAG ingestion handler tests."""

    async def _verify_document_processed(
        self, db_session, document, expected_pages=2
    ):
        from sqlalchemy import select

        await db_session.refresh(document)
        assert document.status == "processed"

        pages_result = await db_session.execute(
            select(RagPage).where(RagPage.document_id == document.id)
        )
        pages = list(pages_result.scalars().all())
        assert len(pages) == expected_pages
        for page in pages:
            assert page.content is not None
            assert page.blob_path is not None

        chunks_result = await db_session.execute(
            select(RagChunk).where(
                RagChunk.document_id == document.id,
                RagChunk.status == "active",
            )
        )
        chunks = list(chunks_result.scalars().all())
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 1536
            assert chunk.status == "active"

        return pages, chunks

    async def _run_handler(self, db_session, document, mocks: dict):
        """Run the handler with given mocks applied."""
        handler_path = "handlers.rag"

        with patch.multiple(
            handler_path,
            get_rag_bucket=mocks["get_rag_bucket"],
            download_object=mocks["download_object"],
            upload_object=mocks["upload_object"],
            delete_object=mocks["delete_object"],
            get_embedding_provider=mocks["get_embedding_provider"],
            extract_text_from_pdf=mocks["extract_text_from_pdf"],
            create_chunks_from_pages=mocks["create_chunks_from_pages"],
            apply_rls_context_to_session=AsyncMock(),
        ), patch.object(
            type(db_session), "close", MagicMock()
        ):
            with patch(f"{handler_path}.async_session_factory") as mock_factory:
                mock_factory.return_value.__aenter__.return_value = db_session
                mock_factory.return_value.__aexit__.return_value = None

                from handlers.rag import handle_rag_document_uploaded

                await handle_rag_document_uploaded({
                    "document_id": str(document.id),
                    "tenant_id": str(document.tenant_id),
                    "blob_path": document.blob_path,
                })

    async def test_pending_document_creates_pages_and_chunks(
        self, db_session, pending_document
    ):
        """T015: Worker processes a pending document, creating pages and chunks."""
        mocks = {
            "get_rag_bucket": MagicMock(),
            "download_object": MagicMock(return_value=b"%PDF-1.4\nfake\n%%EOF\n"),
            "upload_object": MagicMock(),
            "delete_object": MagicMock(),
            "get_embedding_provider": MagicMock(
                return_value=AsyncMock(embed=AsyncMock(return_value=[FAKE_EMBEDDING, FAKE_EMBEDDING]))
            ),
            "extract_text_from_pdf": MagicMock(return_value=["page one text", "page two text"]),
            "create_chunks_from_pages": _mock_create_chunks,
        }

        await self._run_handler(db_session, pending_document, mocks)

        await self._verify_document_processed(db_session, pending_document, expected_pages=2)

    async def test_unchanged_document_reuses_chunks(
        self, db_session, pending_document
    ):
        """T016: Re-ingesting an unchanged document reuses existing chunks
        instead of creating new ones or re-embedding."""
        from sqlalchemy import select

        mocks = {
            "get_rag_bucket": MagicMock(),
            "download_object": MagicMock(return_value=b"%PDF-1.4\nfake\n%%EOF\n"),
            "upload_object": MagicMock(),
            "delete_object": MagicMock(),
            "get_embedding_provider": MagicMock(
                return_value=AsyncMock(embed=AsyncMock(return_value=[FAKE_EMBEDDING]))
            ),
            "extract_text_from_pdf": MagicMock(return_value=["stable page text"]),
            "create_chunks_from_pages": _mock_create_chunks,
        }

        # First ingestion
        await self._run_handler(db_session, pending_document, mocks)

        await db_session.refresh(pending_document)
        assert pending_document.status == "processed"

        first_chunks = await db_session.execute(
            select(RagChunk).where(RagChunk.document_id == pending_document.id)
        )
        first_list = list(first_chunks.scalars().all())
        first_ids = {c.id for c in first_list}
        first_hashes = {c.content_hash for c in first_list if c.status == "active"}

        # Reset to trigger re-ingestion
        pending_document.status = "pending"
        await db_session.commit()

        # Embedding provider should NOT be called (all hashes reused)
        reused_mocks = {**mocks}
        reused_mocks["get_embedding_provider"] = MagicMock(
            return_value=AsyncMock(embed=AsyncMock(side_effect=RuntimeError("should not be called")))
        )

        # Second ingestion (same content)
        await self._run_handler(db_session, pending_document, reused_mocks)

        second_chunks = await db_session.execute(
            select(RagChunk).where(RagChunk.document_id == pending_document.id)
        )
        second_list = list(second_chunks.scalars().all())
        second_active_ids = {c.id for c in second_list if c.status == "active"}
        second_hashes = {c.content_hash for c in second_list if c.status == "active"}

        # Same hashes present
        assert second_hashes == first_hashes
        # No new chunk rows created
        assert second_active_ids == first_ids

    async def test_modified_document_orphans_old_chunks(
        self, db_session, pending_document
    ):
        """T017: Re-ingesting a modified document orphans the old, now-unused
        chunks. Active chunks contain the new content only."""
        from sqlalchemy import select

        mocks = {
            "get_rag_bucket": MagicMock(),
            "download_object": MagicMock(return_value=b"%PDF-1.4\nfake\n%%EOF\n"),
            "upload_object": MagicMock(),
            "delete_object": MagicMock(),
            "get_embedding_provider": MagicMock(
                return_value=AsyncMock(embed=AsyncMock(return_value=[FAKE_EMBEDDING]))
            ),
            "extract_text_from_pdf": MagicMock(return_value=["original page text"]),
            "create_chunks_from_pages": _mock_create_chunks,
        }

        # First ingestion
        await self._run_handler(db_session, pending_document, mocks)

        await db_session.refresh(pending_document)
        assert pending_document.status == "processed"

        first_active = await db_session.execute(
            select(RagChunk).where(
                RagChunk.document_id == pending_document.id,
                RagChunk.status == "active",
            )
        )
        first_active_set = {c.content_hash for c in first_active.scalars().all()}

        # Reset for re-ingestion with different content
        pending_document.status = "pending"
        await db_session.commit()

        modified_mocks = {**mocks}
        modified_mocks["extract_text_from_pdf"] = MagicMock(
            return_value=["completely different page content"]
        )

        # Second ingestion
        await self._run_handler(db_session, pending_document, modified_mocks)

        all_chunks = await db_session.execute(
            select(RagChunk).where(RagChunk.document_id == pending_document.id)
        )
        all_list = list(all_chunks.scalars().all())

        second_active = {c.content_hash for c in all_list if c.status == "active"}
        orphaned = {c.content_hash for c in all_list if c.status == "orphaned"}

        # New active hashes are entirely different
        assert first_active_set.isdisjoint(second_active)
        # Old active chunks moved to orphaned
        assert orphaned == first_active_set
