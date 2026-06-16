"""Agency AI worker handlers.

Phase 12 events:
- agency_ai.spec_sheet_uploaded: Run OCR on a temporary spec sheet and
  update the related AgencyAIJob with extracted specs.

The listing draft, lead reply draft, and comparison summary flows run
synchronously in the API process for this phase, so they don't need a
worker event yet. The handler is registered so future async/queued
flows can plug in without changing the worker entry point.
"""

from __future__ import annotations

import logging
from uuid import UUID

import asyncpg
import app.users.models  # noqa: F401 - load users metadata for audit foreign keys

logger = logging.getLogger("worker.agency_ai")


async def handle_agency_ai_spec_sheet_uploaded(
    conn: asyncpg.Connection,
    payload: dict,
    event_id: str | None = None,
) -> None:
    """Run OCR for a queued spec-sheet extraction job."""
    job_id = payload.get("job_id")
    blob_path = payload.get("blob_path")
    content_type = payload.get("content_type")
    if not job_id or not blob_path:
        logger.error("Missing job_id or blob_path in payload: %s", payload)
        return

    job_uuid = UUID(job_id)
    logger.info("Running spec extraction for job %s", job_id)

    try:
        from app.ai.service import AgencyAIService
        from app.common.database import async_session_factory
        from app.common.rls import apply_rls_context_to_session
        from app.common.storage import delete_object, download_object, get_rag_bucket
        from uuid import uuid5, NAMESPACE_DNS

        WORKER_ACTOR = uuid5(NAMESPACE_DNS, "akarai-agency-ai-worker")

        bucket = get_rag_bucket()
        file_bytes = download_object(bucket, blob_path)

        async with async_session_factory() as session:
            try:
                job_row = await conn.fetchrow(
                    "SELECT tenant_id FROM agency_ai_jobs WHERE id = $1::uuid",
                    job_id,
                )
            except Exception:
                job_row = None

            tenant_id = job_row["tenant_id"] if job_row else None
            if tenant_id is not None:
                try:
                    await apply_rls_context_to_session(
                        session,
                        tenant_id=UUID(str(tenant_id)),
                        user_id=WORKER_ACTOR,
                        role="agency_ai_worker",
                        is_platform_admin=False,
                    )
                except Exception:
                    pass

            service = AgencyAIService(session)
            await service.run_spec_extraction(
                job_uuid,
                file_bytes=file_bytes,
                content_type=content_type,
            )
        try:
            delete_object(bucket, blob_path)
        except Exception:
            logger.warning("Failed to clean temporary spec sheet for job %s", job_id)
    except Exception:
        logger.exception("Failed to process spec sheet for job %s", job_id)
        raise
