"""Database outbox polling with fenced leases and consumer idempotency."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import random
from contextlib import suppress
from typing import Any

import asyncpg

logger = logging.getLogger("worker.outbox")

OUTBOX_PENDING = "pending"
OUTBOX_PROCESSING = "processing"
OUTBOX_DELIVERED = "delivered"
OUTBOX_FAILED = "failed"
OUTBOX_DEAD_LETTER = "dead_letter"

INBOX_PROCESSING = "processing"
INBOX_CONSUMED = "consumed"
INBOX_FAILED = "failed"

LEASE_SECONDS = max(1, int(os.getenv("OUTBOX_LEASE_SECONDS", "900")))
HEARTBEAT_SECONDS = max(1, LEASE_SECONDS // 3)


class NonRetryableEventError(Exception):
    """Signals an event that cannot succeed on a later delivery attempt."""


async def claim_and_dispatch(
    conn: asyncpg.Connection,
    handlers: dict[str, Any],
    lease_conn: asyncpg.Connection | None = None,
    dead_letter_handlers: dict[str, Any] | None = None,
) -> bool:
    dead_letter_handlers = dead_letter_handlers or {}
    await _recover_expired_claims(conn, dead_letter_handlers)
    event = await _claim_pending_event(conn)
    if event is None:
        return False

    event_id = event["id"]
    claim_token = event["claim_token"]
    event_name = event["event_name"]
    handler = handlers.get(event_name)
    if handler is None:
        await _retry_or_dead_letter(
            conn,
            event,
            f"no handler registered for '{event_name}'",
            dead_letter_handlers,
        )
        return True

    consumer_name = f"worker:{event_name}"
    inbox_state = await _claim_inbox_event(conn, event_id, consumer_name, claim_token)
    if inbox_state == INBOX_CONSUMED:
        await _mark_delivered(conn, event_id, claim_token)
        return True
    if inbox_state is None:
        await _retry_or_dead_letter(
            conn,
            event,
            "consumer is still processing this event",
            dead_letter_handlers,
        )
        return True

    try:
        await _run_handler_with_heartbeat(
            conn,
            handler,
            _decode_payload(event["payload"]),
            event_id,
            claim_token,
            consumer_name,
            lease_conn,
        )
        if not await _mark_inbox_consumed(conn, event_id, consumer_name, claim_token):
            logger.warning("Lost inbox claim before completion for event %s", event_id)
            return True
        if not await _mark_delivered(conn, event_id, claim_token):
            logger.warning("Lost outbox claim before completion for event %s", event_id)
        return True
    except NonRetryableEventError as exc:
        await _mark_inbox_failed(conn, event_id, consumer_name, claim_token, str(exc))
        await _dead_letter_event(conn, event, str(exc), dead_letter_handlers)
        logger.error("Dead-lettered non-retryable event %s: %s", event_id, exc)
        return True
    except Exception as exc:
        await _mark_inbox_failed(conn, event_id, consumer_name, claim_token, str(exc))
        await _retry_or_dead_letter(conn, event, str(exc), dead_letter_handlers)
        logger.exception("Handler failed for event '%s' (id=%s)", event_name, event_id)
        return True


def _decode_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        return json.loads(payload)
    if isinstance(payload, dict):
        return payload
    raise NonRetryableEventError("outbox payload is not a JSON object")


async def _run_handler_with_heartbeat(
    conn: asyncpg.Connection,
    handler: Any,
    payload: dict[str, Any],
    event_id: str,
    claim_token: str,
    consumer_name: str,
    lease_conn: asyncpg.Connection | None,
) -> None:
    heartbeat = None
    if lease_conn is not None:
        heartbeat = asyncio.create_task(_heartbeat_claim(lease_conn, event_id, claim_token, consumer_name))
    try:
        invocation = _invoke_handler(handler, conn, payload, event_id)
        if inspect.isawaitable(invocation):
            await invocation
    finally:
        if heartbeat is not None:
            heartbeat.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat


def _invoke_handler(handler: Any, conn: asyncpg.Connection, payload: dict[str, Any], event_id: str) -> Any:
    parameter_count = len(inspect.signature(handler).parameters)
    if parameter_count <= 1:
        return handler(payload)
    if parameter_count == 2:
        return handler(conn, payload)
    return handler(conn, payload, event_id)


async def _heartbeat_claim(
    conn: asyncpg.Connection,
    event_id: str,
    claim_token: str,
    consumer_name: str,
) -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_SECONDS)
        outbox_updated = await conn.execute(
            """
            UPDATE outbox_events
            SET lease_expires_at = NOW() + ($1 * INTERVAL '1 second'), updated_at = NOW()
            WHERE id = $2::uuid AND claim_token = $3::uuid AND status = $4
            """,
            LEASE_SECONDS,
            event_id,
            claim_token,
            OUTBOX_PROCESSING,
        )
        inbox_updated = await conn.execute(
            """
            UPDATE inbox_events
            SET lease_expires_at = NOW() + ($1 * INTERVAL '1 second'), updated_at = NOW()
            WHERE event_id = $2
              AND consumer_name = $3
              AND idempotency_key = $4
              AND claim_token = $5::uuid
              AND status = $6
            """,
            LEASE_SECONDS,
            event_id,
            consumer_name,
            f"outbox:{event_id}",
            claim_token,
            INBOX_PROCESSING,
        )
        if outbox_updated == "UPDATE 0" or inbox_updated == "UPDATE 0":
            logger.warning("Lease heartbeat lost ownership for event %s", event_id)
            return


async def _recover_expired_claims(
    conn: asyncpg.Connection,
    dead_letter_handlers: dict[str, Any],
) -> None:
    while event := await _claim_expired_event(conn):
        await _retry_or_dead_letter(
            conn,
            event,
            "processing lease expired",
            dead_letter_handlers,
        )


async def _claim_expired_event(conn: asyncpg.Connection) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        WITH candidate AS (
            SELECT id
            FROM outbox_events
            WHERE status = $1 AND lease_expires_at <= NOW()
            ORDER BY lease_expires_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE outbox_events
        SET claimed_at = NOW(),
            lease_expires_at = NOW() + ($2 * INTERVAL '1 second'),
            claim_token = gen_random_uuid(),
            updated_at = NOW()
        WHERE id = (SELECT id FROM candidate)
        RETURNING id::text, claim_token::text, event_name, payload, retry_count, max_retries
        """,
        OUTBOX_PROCESSING,
        LEASE_SECONDS,
    )


async def _claim_pending_event(conn: asyncpg.Connection) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        WITH candidate AS (
            SELECT id
            FROM outbox_events
            WHERE status = $1 AND available_at <= NOW()
            ORDER BY available_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE outbox_events
        SET status = $2,
            claimed_at = NOW(),
            lease_expires_at = NOW() + ($3 * INTERVAL '1 second'),
            claim_token = gen_random_uuid(),
            updated_at = NOW()
        WHERE id = (SELECT id FROM candidate)
        RETURNING id::text, claim_token::text, event_name, payload, retry_count, max_retries
        """,
        OUTBOX_PENDING,
        OUTBOX_PROCESSING,
        LEASE_SECONDS,
    )


async def _claim_inbox_event(
    conn: asyncpg.Connection,
    event_id: str,
    consumer_name: str,
    claim_token: str,
) -> str | None:
    idempotency_key = f"outbox:{event_id}"
    inserted = await conn.fetchrow(
        """
        INSERT INTO inbox_events
        (id, event_id, consumer_name, idempotency_key, status, received_at, lease_expires_at, claim_token, created_at, updated_at)
        VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW(), NOW() + ($5 * INTERVAL '1 second'), $6::uuid, NOW(), NOW())
        ON CONFLICT (consumer_name, idempotency_key) DO NOTHING
        RETURNING status
        """,
        event_id,
        consumer_name,
        idempotency_key,
        INBOX_PROCESSING,
        LEASE_SECONDS,
        claim_token,
    )
    if inserted is not None:
        return INBOX_PROCESSING

    existing = await conn.fetchrow(
        """
        SELECT status, lease_expires_at
        FROM inbox_events
        WHERE consumer_name = $1 AND idempotency_key = $2
        """,
        consumer_name,
        idempotency_key,
    )
    if existing is None:
        raise RuntimeError("inbox event disappeared after a duplicate insert")
    if existing["status"] == INBOX_CONSUMED:
        return INBOX_CONSUMED
    if (
        existing["status"] == INBOX_PROCESSING
        and existing["lease_expires_at"] is not None
        and existing["lease_expires_at"] > await conn.fetchval("SELECT NOW()")
    ):
        return None

    reclaimed = await conn.fetchrow(
        """
        UPDATE inbox_events
        SET status = $1,
            lease_expires_at = NOW() + ($2 * INTERVAL '1 second'),
            claim_token = $3::uuid,
            last_error = NULL,
            updated_at = NOW()
        WHERE consumer_name = $4
          AND idempotency_key = $5
          AND status <> $6
          AND (lease_expires_at <= NOW() OR status = $7)
        RETURNING status
        """,
        INBOX_PROCESSING,
        LEASE_SECONDS,
        claim_token,
        consumer_name,
        idempotency_key,
        INBOX_CONSUMED,
        INBOX_FAILED,
    )
    return INBOX_PROCESSING if reclaimed is not None else None


async def _mark_inbox_consumed(conn: asyncpg.Connection, event_id: str, consumer_name: str, claim_token: str) -> bool:
    status = await conn.execute(
        """
        UPDATE inbox_events
        SET status = $1, processed_at = NOW(), lease_expires_at = NULL, claim_token = NULL, updated_at = NOW()
        WHERE event_id = $2 AND consumer_name = $3 AND idempotency_key = $4 AND claim_token = $5::uuid
        """,
        INBOX_CONSUMED,
        event_id,
        consumer_name,
        f"outbox:{event_id}",
        claim_token,
    )
    return status == "UPDATE 1"


async def _mark_inbox_failed(
    conn: asyncpg.Connection,
    event_id: str,
    consumer_name: str,
    claim_token: str,
    error: str,
) -> bool:
    status = await conn.execute(
        """
        UPDATE inbox_events
        SET status = $1, lease_expires_at = NULL, claim_token = NULL, last_error = $2, updated_at = NOW()
        WHERE event_id = $3 AND consumer_name = $4 AND idempotency_key = $5 AND claim_token = $6::uuid
        """,
        INBOX_FAILED,
        error[:2000],
        event_id,
        consumer_name,
        f"outbox:{event_id}",
        claim_token,
    )
    return status == "UPDATE 1"


async def _mark_delivered(conn: asyncpg.Connection, event_id: str, claim_token: str) -> bool:
    status = await conn.execute(
        """
        UPDATE outbox_events
        SET status = $1,
            processed_at = NOW(),
            claimed_at = NULL,
            lease_expires_at = NULL,
            claim_token = NULL,
            updated_at = NOW()
        WHERE id = $2::uuid AND claim_token = $3::uuid AND status = $4
        """,
        OUTBOX_DELIVERED,
        event_id,
        claim_token,
        OUTBOX_PROCESSING,
    )
    return status == "UPDATE 1"


async def _mark_retry(
    conn: asyncpg.Connection,
    event_id: str,
    claim_token: str,
    retry_count: int,
    *,
    last_error: str,
) -> bool:
    next_retry = retry_count + 1
    delay_seconds = min(300, 5 * (2 ** max(0, retry_count)))
    delay_seconds *= random.uniform(0.75, 1.25)
    status = await conn.execute(
        """
        UPDATE outbox_events
        SET status = $1,
            retry_count = $2,
            last_error = $3,
            available_at = NOW() + ($4 * INTERVAL '1 second'),
            claimed_at = NULL,
            lease_expires_at = NULL,
            claim_token = NULL,
            updated_at = NOW()
        WHERE id = $5::uuid AND claim_token = $6::uuid AND status = $7
        """,
        OUTBOX_PENDING,
        next_retry,
        last_error[:2000],
        delay_seconds,
        event_id,
        claim_token,
        OUTBOX_PROCESSING,
    )
    return status == "UPDATE 1"


async def _retry_or_dead_letter(
    conn: asyncpg.Connection,
    event: asyncpg.Record,
    error: str,
    dead_letter_handlers: dict[str, Any],
) -> bool:
    if event["retry_count"] + 1 < event["max_retries"]:
        return await _mark_retry(
            conn,
            event["id"],
            event["claim_token"],
            event["retry_count"],
            last_error=error,
        )
    return await _dead_letter_event(conn, event, error, dead_letter_handlers, retry_count=event["retry_count"] + 1)


async def _dead_letter_event(
    conn: asyncpg.Connection,
    event: asyncpg.Record,
    error: str,
    dead_letter_handlers: dict[str, Any],
    *,
    retry_count: int | None = None,
) -> bool:
    finalizer = dead_letter_handlers.get(event["event_name"])
    if finalizer is not None:
        try:
            await _invoke_dead_letter_handler(
                finalizer,
                conn,
                _decode_payload(event["payload"]),
                event["id"],
                error,
                retry_count if retry_count is not None else event["retry_count"],
            )
        except Exception as finalizer_error:
            logger.exception("Dead-letter finalizer failed for event %s", event["id"])
            return await _release_claim_for_finalizer_retry(conn, event, str(finalizer_error))
    return await _mark_dead_letter(
        conn,
        event["id"],
        event["claim_token"],
        error,
        retry_count=retry_count,
    )


async def _invoke_dead_letter_handler(
    finalizer: Any,
    conn: asyncpg.Connection,
    payload: dict[str, Any],
    event_id: str,
    error: str,
    retry_count: int,
) -> None:
    invocation = finalizer(
        conn,
        payload,
        event_id,
        {"error": error[:2000], "retry_count": retry_count},
    )
    if inspect.isawaitable(invocation):
        await invocation


async def _release_claim_for_finalizer_retry(
    conn: asyncpg.Connection,
    event: asyncpg.Record,
    error: str,
) -> bool:
    status = await conn.execute(
        """
        UPDATE outbox_events
        SET status = $1,
            available_at = NOW() + INTERVAL '5 seconds',
            claimed_at = NULL,
            lease_expires_at = NULL,
            claim_token = NULL,
            last_error = $2,
            updated_at = NOW()
        WHERE id = $3::uuid AND claim_token = $4::uuid AND status = $5
        """,
        OUTBOX_PENDING,
        f"dead-letter finalizer failed: {error}"[:2000],
        event["id"],
        event["claim_token"],
        OUTBOX_PROCESSING,
    )
    return status == "UPDATE 1"


async def _mark_dead_letter(
    conn: asyncpg.Connection,
    event_id: str,
    claim_token: str,
    error: str,
    *,
    retry_count: int | None = None,
) -> bool:
    retry_clause = "retry_count = $2," if retry_count is not None else ""
    arguments: list[Any] = [OUTBOX_DEAD_LETTER]
    if retry_count is not None:
        arguments.append(retry_count)
    arguments.extend([error[:2000], event_id, claim_token, OUTBOX_PROCESSING])
    status = await conn.execute(
        f"""
        UPDATE outbox_events
        SET status = $1,
            {retry_clause}
            last_error = ${len(arguments) - 3},
            available_at = NOW(),
            claimed_at = NULL,
            lease_expires_at = NULL,
            claim_token = NULL,
            updated_at = NOW()
        WHERE id = ${len(arguments) - 2}::uuid
          AND claim_token = ${len(arguments) - 1}::uuid
          AND status = ${len(arguments)}
        """,
        *arguments,
    )
    return status == "UPDATE 1"
