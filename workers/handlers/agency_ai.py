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

import app.users.models  # noqa: F401 - load users metadata for audit foreign keys
import asyncpg
from outbox import NonRetryableEventError

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
        raise NonRetryableEventError(
            "agency_ai.spec_sheet_uploaded payload is missing required fields"
        )

    try:
        job_uuid = UUID(job_id)
    except ValueError as exc:
        raise NonRetryableEventError("agency_ai.spec_sheet_uploaded job_id is invalid") from exc
    logger.info("Running spec extraction for job %s", job_id)

    try:
        from uuid import NAMESPACE_DNS, uuid5

        from app.ai.service import AgencyAIService
        from app.common.database import async_session_factory
        from app.common.rls import apply_rls_context_to_session
        from app.common.storage import delete_object, download_object, get_rag_bucket

        WORKER_ACTOR = uuid5(NAMESPACE_DNS, "akarai-agency-ai-worker")

        bucket = get_rag_bucket()
        file_bytes = download_object(bucket, blob_path)

        async with async_session_factory() as session:
            job_row = await conn.fetchrow(
                "SELECT tenant_id, status FROM agency_ai_jobs WHERE id = $1::uuid",
                job_id,
            )

            if job_row is None:
                raise NonRetryableEventError(f"Agency AI job {job_id} no longer exists")
            if job_row["status"] in {"completed", "failed", "blocked"}:
                logger.info("Agency AI job %s is already terminal", job_id)
                return

            tenant_id = job_row["tenant_id"]
            if tenant_id is None:
                raise NonRetryableEventError(f"Agency AI job {job_id} is missing a tenant")
            await apply_rls_context_to_session(
                session,
                tenant_id=UUID(str(tenant_id)),
                user_id=WORKER_ACTOR,
                role="agency_ai_worker",
                is_platform_admin=False,
            )

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


async def finalize_agency_ai_spec_sheet_dead_letter(
    conn: asyncpg.Connection,
    payload: dict,
    _event_id: str,
    failure: dict,
) -> None:
    job_id = payload.get("job_id")
    if not job_id:
        return
    try:
        UUID(str(job_id))
    except ValueError:
        return
    await conn.execute(
        """
        UPDATE agency_ai_jobs
        SET status = 'failed', completed_at = NOW(), error_message = $1
        WHERE id = $2::uuid AND status NOT IN ('completed', 'blocked')
        """,
        str(failure["error"])[:1024],
        str(job_id),
    )
