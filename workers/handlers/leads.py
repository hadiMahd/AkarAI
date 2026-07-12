"""Worker handler for lead.created — forwards to model service for classification."""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import asyncpg
from outbox import NonRetryableEventError

logger = logging.getLogger("worker.handlers.leads")

async def handle_lead_created(_conn, payload: dict[str, Any], _event_id: str) -> dict[str, Any]:
    """Forward lead to the model service for two-stage classification."""
    lead_id = payload.get("lead_id")
    tenant_id = payload.get("tenant_id")
    if not lead_id or not tenant_id:
        raise NonRetryableEventError("lead.created payload is missing required fields")
    try:
        UUID(str(lead_id))
        UUID(str(tenant_id))
    except ValueError as exc:
        raise NonRetryableEventError("lead.created payload contains invalid UUIDs") from exc

    logger.info("Handling lead.created for lead=%s tenant=%s", lead_id, tenant_id)

    # Skip empty messages — they were already classified as spam inline
    message = payload.get("message")
    if not message or not str(message).strip():
        logger.info(
            "Lead %s has empty message — already classified as spam inline, skipping model service",
            lead_id,
        )
        return {
            "lead_id": lead_id,
            "status": "skipped_empty_message",
            "spam_label": "spam",
        }

    from handlers.lead_processing_client import forward_to_model_service

    result = await forward_to_model_service(
        lead_id=str(lead_id),
        tenant_id=str(tenant_id),
        message=str(message),
        name=payload.get("name"),
        email=payload.get("email"),
    )

    logger.info(
        "Model service completed for lead=%s: spam=%s level=%s",
        lead_id,
        result.get("spam_result", {}).get("label"),
        (result.get("level_result") or {}).get("label"),
    )
    return {
        "lead_id": lead_id,
        "status": "classified",
        "spam_result": result.get("spam_result"),
        "level_result": result.get("level_result"),
    }


async def finalize_lead_created_dead_letter(
    conn: asyncpg.Connection,
    payload: dict[str, Any],
    _event_id: str,
    failure: dict[str, Any],
) -> None:
    lead_id = payload.get("lead_id")
    tenant_id = payload.get("tenant_id")
    if not lead_id or not tenant_id:
        return
    try:
        UUID(str(lead_id))
        UUID(str(tenant_id))
    except ValueError:
        return

    error = str(failure["error"])[:2000]
    retry_count = int(failure["retry_count"])
    async with conn.transaction():
        await conn.execute(
            """
            UPDATE lead_spam_results
            SET status = 'failed', last_error = $1, retry_count = $2
            WHERE lead_id = $3::uuid AND agency_tenant_id = $4::uuid AND status <> 'completed'
            """,
            error,
            retry_count,
            str(lead_id),
            str(tenant_id),
        )
        await conn.execute(
            """
            UPDATE lead_level_results
            SET status = 'failed', last_error = $1, retry_count = $2
            WHERE lead_id = $3::uuid AND agency_tenant_id = $4::uuid AND status <> 'completed'
            """,
            error,
            retry_count,
            str(lead_id),
            str(tenant_id),
        )
        await conn.execute(
            """
            UPDATE leads
            SET processing_status = 'failed'
            WHERE id = $1::uuid AND agency_tenant_id = $2::uuid AND processing_status <> 'completed'
            """,
            str(lead_id),
            str(tenant_id),
        )
