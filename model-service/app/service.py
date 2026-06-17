"""Two-stage inference orchestration for lead classification."""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx

from app.config import settings
from app.predictors import classify_spam, classify_level
from app.schemas import ClassifyResponse, StageResult, CallbackPayload

logger = logging.getLogger("model-service.service")


async def _send_callback(payload: CallbackPayload) -> None:
    """Post classification result back to the backend callback endpoint."""
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{settings.backend_url}/api/v1/internal/leads/classification-callback",
                json=payload.model_dump(mode="json"),
                headers={
                    "Authorization": f"Bearer {settings.callback_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
    except Exception as e:
        logger.warning(
            "Callback delivery failed for lead=%s stage=%s: %s",
            payload.lead_id,
            payload.stage,
            e,
        )
        raise


async def classify_lead(
    lead_id: UUID,
    tenant_id: UUID,
    message: str = "",
    name: str | None = None,
    email: str | None = None,
) -> ClassifyResponse:
    """Run two-stage classification: spam → Hot/Normal for non-spam."""
    logger.info("Classifying lead=%s for tenant=%s", lead_id, tenant_id)

    # Stage 1: Spam detection
    spam_result = classify_spam(message, name, email)
    spam_stage = StageResult(
        stage="spam",
        status=spam_result["status"],
        label=spam_result.get("label"),
        score=spam_result.get("score"),
        details=spam_result.get("details"),
    )

    # Send spam callback
    await _send_callback(CallbackPayload(
        lead_id=lead_id,
        tenant_id=tenant_id,
        stage="spam",
        status=spam_stage.status,
        label=spam_stage.label,
        score=spam_stage.score,
        details=spam_stage.details,
    ))

    # Stage 2: Hot/Normal only for non-spam leads
    level_stage: StageResult | None = None
    if spam_result.get("label") != "spam":
        level_result = classify_level(message, name)
        level_stage = StageResult(
            stage="level",
            status=level_result["status"],
            label=level_result.get("level"),
            score=level_result.get("score"),
            details=level_result.get("details"),
        )

        await _send_callback(CallbackPayload(
            lead_id=lead_id,
            tenant_id=tenant_id,
            stage="level",
            status=level_stage.status,
            label=level_stage.label,
            score=level_stage.score,
            details=level_stage.details,
        ))

    return ClassifyResponse(
        lead_id=lead_id,
        tenant_id=tenant_id,
        spam_result=spam_stage,
        level_result=level_stage,
    )
