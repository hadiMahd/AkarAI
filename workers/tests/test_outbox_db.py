"""Integration test: worker DB outbox flow with foundation.test handler."""

import json
import os

import asyncpg
import pytest
from outbox import (
    OUTBOX_DEAD_LETTER,
    OUTBOX_DELIVERED,
    OUTBOX_FAILED,
    claim_and_dispatch,
)


@pytest.fixture
async def conn():
    url = os.getenv("DATABASE_URL", "postgresql://akarai:akarai@postgres:5432/akarai").replace("+asyncpg", "")
    conn = await asyncpg.connect(url)
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_dispatches_registered_handler(conn):
    await conn.execute("DELETE FROM outbox_events")

    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'foundation.test', 'ik-test-001', '{"hello":"world"}', 'pending', NOW())
    """)

    dispatched = []

    def test_handler(payload):
        dispatched.append(payload)

    processed = await claim_and_dispatch(conn, {"foundation.test": test_handler})
    assert processed is True
    assert len(dispatched) == 1
    assert json.loads(dispatched[0]) == {"hello": "world"}

    row = await conn.fetchrow(
        "SELECT status, processed_at FROM outbox_events WHERE idempotency_key = 'ik-test-001'"
    )
    assert row["status"] == OUTBOX_DELIVERED
    assert row["processed_at"] is not None


@pytest.mark.asyncio
async def test_no_handler_marks_failed(conn):
    await conn.execute("DELETE FROM outbox_events")

    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'ghost.event', 'ik-test-002', '{}', 'pending', NOW())
    """)

    processed = await claim_and_dispatch(conn, {})
    assert processed is True

    row = await conn.fetchrow(
        "SELECT status, last_error FROM outbox_events WHERE idempotency_key = 'ik-test-002'"
    )
    assert row["status"] == OUTBOX_FAILED
    assert "no handler registered" in row["last_error"]


@pytest.mark.asyncio
async def test_handler_exception_retries_then_dead_letter(conn):
    await conn.execute("DELETE FROM outbox_events")

    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at, retry_count, max_retries)
        VALUES (gen_random_uuid(), 'foundation.test', 'ik-test-003', '{}', 'pending', NOW(), 2, 3)
    """)

    called = []

    def failing_handler(payload):
        called.append(payload)
        raise RuntimeError("boom")

    processed = await claim_and_dispatch(conn, {"foundation.test": failing_handler})
    assert processed is True
    assert len(called) == 1

    row = await conn.fetchrow(
        "SELECT status, retry_count, last_error FROM outbox_events WHERE idempotency_key = 'ik-test-003'"
    )
    assert row["status"] == OUTBOX_DEAD_LETTER
    assert row["retry_count"] == 3
    assert "boom" in row["last_error"]


@pytest.mark.asyncio
async def test_no_pending_events_returns_false(conn):
    await conn.execute("DELETE FROM outbox_events")
    processed = await claim_and_dispatch(conn, {"foundation.test": lambda p: None})
    assert processed is False
