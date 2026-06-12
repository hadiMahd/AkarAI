"""Database outbox polling for the worker. Phase 2 — minimal asyncpg-based layer."""

from __future__ import annotations

import inspect
import json
import logging
import random
from typing import Any

import asyncpg

logger = logging.getLogger("worker.outbox")

OUTBOX_PENDING = "pending"
OUTBOX_PROCESSING = "processing"
OUTBOX_DELIVERED = "delivered"
OUTBOX_FAILED = "failed"
OUTBOX_DEAD_LETTER = "dead_letter"


async def claim_and_dispatch(
    conn: asyncpg.Connection,
    handlers: dict[str, Any],
) -> bool:
    row = await _claim_pending_event(conn)
    if row is None:
        return False

    event_name = row["event_name"]
    payload = _decode_payload(row["payload"])
    event_id = row["id"]
    retries = row["retry_count"]
    max_retries = row["max_retries"]

    handler = handlers.get(event_name)

    if handler is None:
        await _mark_retry(conn, event_id, retries, max_retries,
                          last_error=f"no handler registered for '{event_name}'")
        logger.warning("No handler for event '%s' (id=%s) — retry %s/%s",
                       event_name, event_id, retries + 1, max_retries)
        return True

    try:
        result = await _invoke_handler(handler, conn, payload, event_id)
        if inspect.isawaitable(result):
            await result
        await _mark_delivered(conn, event_id)
        logger.info("Dispatched event '%s' (id=%s)", event_name, event_id)
    except Exception as exc:
        await _mark_retry(conn, event_id, retries, max_retries, last_error=str(exc))
        logger.error("Handler failed for event '%s' (id=%s): %s", event_name, event_id, exc)

    return True


def _decode_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        return json.loads(payload)
    if isinstance(payload, dict):
        return payload
    return {"_raw": str(payload)}


async def _invoke_handler(handler: Any, conn: asyncpg.Connection, payload: dict[str, Any], event_id: str) -> Any:
    sig = inspect.signature(handler)
    params = list(sig.parameters.values())

    if len(params) <= 1:
        return handler(payload)
    if len(params) == 2:
        return handler(conn, payload)
    return handler(conn, payload, event_id)


async def _claim_pending_event(conn: asyncpg.Connection) -> dict[str, Any] | None:
    return await conn.fetchrow("""
        WITH claimed AS (
            SELECT id FROM outbox_events
            WHERE status = $1 AND available_at <= NOW()
            ORDER BY available_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE outbox_events
        SET status = $2, updated_at = NOW()
        WHERE id = (SELECT id FROM claimed)
        RETURNING id::text, event_name, payload, retry_count, max_retries
    """, OUTBOX_PENDING, OUTBOX_PROCESSING)


async def _mark_delivered(conn: asyncpg.Connection, event_id: str) -> None:
    await conn.execute("""
        UPDATE outbox_events
        SET status = $1, processed_at = NOW(), updated_at = NOW()
        WHERE id = $2::uuid
    """, OUTBOX_DELIVERED, event_id)


async def _mark_retry(
    conn: asyncpg.Connection,
    event_id: str,
    retry_count: int,
    max_retries: int,
    *,
    last_error: str = "",
) -> None:
    new_retry = retry_count + 1
    if new_retry >= max_retries:
        status = OUTBOX_DEAD_LETTER
        available_at_seconds = None
    else:
        status = OUTBOX_PENDING
        base_seconds = 5 * (2 ** max(0, retry_count))
        delay_seconds = min(300, base_seconds)
        jittered_seconds = random.uniform(delay_seconds * 0.75, delay_seconds * 1.25)
        available_at_seconds = jittered_seconds
    if available_at_seconds is None:
        await conn.execute("""
            UPDATE outbox_events
            SET status = $1, retry_count = $2, last_error = $3, available_at = NOW(), updated_at = NOW()
            WHERE id = $4::uuid
        """, status, new_retry, last_error, event_id)
    else:
        await conn.execute("""
            UPDATE outbox_events
            SET status = $1, retry_count = $2, last_error = $3, available_at = NOW() + ($4 * INTERVAL '1 second'), updated_at = NOW()
            WHERE id = $5::uuid
        """, status, new_retry, last_error, available_at_seconds, event_id)
        logger.info(
            "Rescheduled event %s after %.1fs (retry %s/%s)",
            event_id,
            available_at_seconds,
            new_retry,
            max_retries,
        )
