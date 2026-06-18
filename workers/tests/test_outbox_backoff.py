"""Backoff and dead-letter behavior for worker outbox retries."""

import os
from datetime import datetime, timezone

import asyncpg
import pytest

from conftest import require_test_database
from outbox import OUTBOX_DEAD_LETTER, OUTBOX_PENDING, claim_and_dispatch


@pytest.fixture
async def conn():
    require_test_database()
    url = os.getenv("DATABASE_URL", "postgresql://akarai:akarai@postgres:5432/akarai").replace("+asyncpg", "")
    conn = await asyncpg.connect(url, statement_cache_size=0)
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_retry_schedules_future_available_at(conn):
    await conn.execute("DELETE FROM outbox_events")
    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'ghost.event', 'backoff-001', '{}', 'pending', NOW())
    """)

    await claim_and_dispatch(conn, {})

    row = await conn.fetchrow(
        "SELECT status, retry_count, available_at FROM outbox_events WHERE idempotency_key = 'backoff-001'"
    )
    assert row["status"] == OUTBOX_PENDING
    assert row["retry_count"] == 1
    assert row["available_at"] > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_retry_hits_dead_letter_at_max_retries(conn):
    await conn.execute("DELETE FROM outbox_events")
    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at, retry_count, max_retries)
        VALUES (gen_random_uuid(), 'ghost.event', 'backoff-002', '{}', 'pending', NOW(), 2, 3)
    """)

    await claim_and_dispatch(conn, {})

    row = await conn.fetchrow(
        "SELECT status, retry_count FROM outbox_events WHERE idempotency_key = 'backoff-002'"
    )
    assert row["status"] == OUTBOX_DEAD_LETTER
    assert row["retry_count"] == 3
