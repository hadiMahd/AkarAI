"""Database outbox polling for the worker. Phase 2 — minimal asyncpg-based layer."""

from __future__ import annotations

import json
import logging
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
        handler(payload)
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
    else:
        status = OUTBOX_PENDING
    await conn.execute("""
        UPDATE outbox_events
        SET status = $1, retry_count = $2, last_error = $3, updated_at = NOW()
        WHERE id = $4::uuid
    """, status, new_retry, last_error, event_id)
