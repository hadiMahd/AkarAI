"""Worker handler for lead.created — forwards to model service for classification."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("worker.handlers.leads")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
CALLBACK_TOKEN = os.getenv("LEAD_MODEL_SERVICE_CALLBACK_TOKEN", "")


async def _post_fail_open_callback(
    lead_id: str,
    tenant_id: str,
    stage: str,
    label: str,
    details: dict[str, Any],
    idempotency_key: str,
) -> None:
    """Post a fail-open completion callback to the backend."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/internal/leads/classification-callback",
            json={
                "lead_id": lead_id,
                "tenant_id": tenant_id,
                "stage": stage,
                "status": "completed",
                "label": label,
                "score": 0.0,
                "details": details,
                "retry_count": 0,
            },
            headers={
                "Authorization": f"Bearer {CALLBACK_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()


async def handle_lead_created(payload: dict[str, Any]) -> dict[str, Any]:
    """Forward lead to the model service for two-stage classification.

    If the model service is unreachable after retries, posts fail-open
    callbacks (not_spam + normal) so the lead never stays pending forever.
    """
    lead_id = payload.get("lead_id", "unknown")
    tenant_id = payload.get("tenant_id", "unknown")

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

    try:
        from handlers.lead_processing_client import forward_to_model_service

        result = await forward_to_model_service(
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            message=str(message) if message else "",
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

    except Exception as e:
        logger.exception("Lead classification failed for lead=%s: %s", lead_id, e)

        # ── Fail-open: post synthetic completion callbacks ──
        fail_reason = {"reason": "model_service_unreachable_fail_open", "error": str(e)[:500]}

        logger.info(
            "Posting fail-open callbacks for lead=%s (spam=not_spam, level=normal)",
            lead_id,
        )

        await _post_fail_open_callback(
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            stage="spam",
            label="not_spam",
            details=fail_reason,
            idempotency_key=f"worker_failopen_{lead_id}_spam",
        )
        await _post_fail_open_callback(
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            stage="level",
            label="normal",
            details=fail_reason,
            idempotency_key=f"worker_failopen_{lead_id}_level",
        )

        return {
            "lead_id": lead_id,
            "status": "fail_open_completed",
            "error": str(e),
        }
