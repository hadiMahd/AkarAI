"""HTTP client for forwarding lead-processing jobs to the model service."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("worker.lead_processing")

DEFAULT_MODEL_SERVICE_URL = os.getenv("LEAD_MODEL_SERVICE_URL", "http://lead-model-service:8100")
DEFAULT_REQUEST_TIMEOUT = int(os.getenv("LEAD_MODEL_SERVICE_REQUEST_TIMEOUT_SECONDS", "120"))
DEFAULT_RETRY_MAX = int(os.getenv("LEAD_PROCESSING_RETRY_MAX_ATTEMPTS", "3"))
DEFAULT_RETRY_BASE = int(os.getenv("LEAD_PROCESSING_RETRY_BASE_DELAY_SECONDS", "5"))
DEFAULT_RETRY_MAX_DELAY = int(os.getenv("LEAD_PROCESSING_RETRY_MAX_DELAY_SECONDS", "120"))


async def _compute_delay(attempt: int) -> float:
    base = DEFAULT_RETRY_BASE * (2 ** max(0, attempt - 1))
    return min(base, DEFAULT_RETRY_MAX_DELAY)


async def forward_to_model_service(
    *,
    lead_id: str,
    tenant_id: str,
    message: str | None = None,
    name: str | None = None,
    email: str | None = None,
    service_url: str = DEFAULT_MODEL_SERVICE_URL,
    max_attempts: int = DEFAULT_RETRY_MAX,
) -> dict[str, Any]:
    """Forward a lead to the model service for spam + Hot/Normal classification.

    Returns a dict with classification results, or raises on exhausted retries.
    """
    payload: dict[str, Any] = {
        "lead_id": lead_id,
        "tenant_id": tenant_id,
        "message": message or "",
        "name": name,
        "email": email,
    }

    last_error: str | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{service_url}/classify",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                logger.info(
                    "Model service classification complete for lead=%s (attempt=%d)",
                    lead_id,
                    attempt,
                )
                return data

        except httpx.HTTPStatusError as e:
            last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.warning(
                "Model service unavailable for lead=%s (attempt=%d/%d): %s",
                lead_id,
                attempt,
                max_attempts,
                last_error,
            )
        except httpx.RequestError as e:
            last_error = f"Request error: {e}"
            logger.warning(
                "Model service request failed for lead=%s (attempt=%d/%d): %s",
                lead_id,
                attempt,
                max_attempts,
                e,
            )
        except Exception as e:
            last_error = f"Unexpected error: {e}"
            logger.warning(
                "Model service unexpected error for lead=%s (attempt=%d/%d): %s",
                lead_id,
                attempt,
                max_attempts,
                e,
            )

        if attempt < max_attempts:
            delay = await _compute_delay(attempt)
            await asyncio.sleep(delay)

    raise RuntimeError(
        f"Failed to classify lead {lead_id} after {max_attempts} attempts: {last_error}"
    )
