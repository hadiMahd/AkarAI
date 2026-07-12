"""Integration test: worker DB outbox flow with foundation.test handler."""

import asyncio
import os

import asyncpg
import pytest
from conftest import require_test_database
from outbox import (
    OUTBOX_DEAD_LETTER,
    OUTBOX_DELIVERED,
    OUTBOX_PENDING,
    OUTBOX_PROCESSING,
    NonRetryableEventError,
    _heartbeat_claim,
    _mark_delivered,
    claim_and_dispatch,
)


@pytest.fixture
async def conn():
    require_test_database()
    url = os.getenv("DATABASE_URL", "postgresql://akarai:akarai@postgres:5432/akarai").replace(
        "+asyncpg", ""
    )
    conn = await asyncpg.connect(url, statement_cache_size=0)
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
    assert dispatched[0] == {"hello": "world"}

    row = await conn.fetchrow(
        "SELECT status, processed_at FROM outbox_events WHERE idempotency_key = 'ik-test-001'"
    )
    assert row["status"] == OUTBOX_DELIVERED
    assert row["processed_at"] is not None


@pytest.mark.asyncio
async def test_dispatches_async_conn_handler(conn):
    await conn.execute("DELETE FROM outbox_events")

    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'foundation.test', 'ik-test-async-001', '{"hello":"async"}', 'pending', NOW())
    """)

    dispatched = []

    async def async_handler(db_conn, payload, event_id=None):
        dispatched.append((db_conn is conn, payload, event_id))

    processed = await claim_and_dispatch(conn, {"foundation.test": async_handler})
    assert processed is True
    assert len(dispatched) == 1
    assert dispatched[0][0] is True
    assert dispatched[0][1] == {"hello": "async"}
    assert dispatched[0][2] is not None

    row = await conn.fetchrow(
        "SELECT status, processed_at FROM outbox_events WHERE idempotency_key = 'ik-test-async-001'"
    )
    assert row["status"] == OUTBOX_DELIVERED
    assert row["processed_at"] is not None


@pytest.mark.asyncio
async def test_no_handler_rescheduled_as_pending(conn):
    await conn.execute("DELETE FROM outbox_events")

    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'ghost.event', 'ik-test-002', '{}', 'pending', NOW())
    """)

    processed = await claim_and_dispatch(conn, {})
    assert processed is True

    row = await conn.fetchrow(
        "SELECT status, retry_count, last_error FROM outbox_events WHERE idempotency_key = 'ik-test-002'"
    )
    assert row["status"] == OUTBOX_PENDING
    assert row["retry_count"] == 1
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


@pytest.mark.asyncio
async def test_retry_schedule_back_to_pending(conn):
    await conn.execute("DELETE FROM outbox_events")

    await conn.execute("""
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at, retry_count, max_retries)
        VALUES (gen_random_uuid(), 'foundation.test', 'ik-test-004', '{"x":1}', 'pending', NOW(), 0, 3)
    """)

    # First attempt — handler fails
    def flaky(payload):
        raise RuntimeError("flaky")

    processed = await claim_and_dispatch(conn, {"foundation.test": flaky})
    assert processed is True
    row = await conn.fetchrow(
        "SELECT status, retry_count FROM outbox_events WHERE idempotency_key = 'ik-test-004'"
    )
    assert row["status"] == OUTBOX_PENDING
    assert row["retry_count"] == 1

    await conn.execute(
        "UPDATE outbox_events SET available_at = NOW() WHERE idempotency_key = 'ik-test-004'"
    )

    # Second attempt after the scheduled retry becomes available.
    processed = await claim_and_dispatch(conn, {"foundation.test": flaky})
    assert processed is True
    row = await conn.fetchrow(
        "SELECT status, retry_count FROM outbox_events WHERE idempotency_key = 'ik-test-004'"
    )
    assert row["status"] == OUTBOX_PENDING
    assert row["retry_count"] == 2

    await conn.execute(
        "UPDATE outbox_events SET available_at = NOW() WHERE idempotency_key = 'ik-test-004'"
    )

    # Third attempt (hits max_retries=3) -> dead_letter.
    processed = await claim_and_dispatch(conn, {"foundation.test": flaky})
    assert processed is True
    row = await conn.fetchrow(
        "SELECT status, retry_count FROM outbox_events WHERE idempotency_key = 'ik-test-004'"
    )
    assert row["status"] == OUTBOX_DEAD_LETTER
    assert row["retry_count"] == 3


@pytest.mark.asyncio
async def test_expired_processing_claim_requeues_with_retry_budget(conn):
    await conn.execute("DELETE FROM outbox_events")
    await conn.execute(
        """
        INSERT INTO outbox_events
        (id, event_name, idempotency_key, payload, status, available_at, claimed_at, lease_expires_at, claim_token)
        VALUES
        (gen_random_uuid(), 'foundation.test', 'expired-claim-001', '{}', 'processing', NOW(), NOW() - INTERVAL '20 minutes', NOW() - INTERVAL '5 minutes', gen_random_uuid())
        """
    )

    processed = await claim_and_dispatch(conn, {"foundation.test": lambda _: None})

    assert processed is False
    row = await conn.fetchrow(
        "SELECT status, retry_count, claim_token FROM outbox_events WHERE idempotency_key = 'expired-claim-001'"
    )
    assert row["status"] == OUTBOX_PENDING
    assert row["retry_count"] == 1
    assert row["claim_token"] is None


@pytest.mark.asyncio
async def test_consumed_inbox_skips_replayed_delivery(conn):
    await conn.execute("DELETE FROM inbox_events")
    await conn.execute("DELETE FROM outbox_events")
    await conn.execute(
        """
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'foundation.test', 'inbox-replay-001', '{}', 'pending', NOW())
        """
    )
    deliveries = []

    def handler(payload):
        deliveries.append(payload)

    await claim_and_dispatch(conn, {"foundation.test": handler})
    await conn.execute(
        """
        UPDATE outbox_events
        SET status = 'pending', processed_at = NULL, available_at = NOW(), claimed_at = NULL,
            lease_expires_at = NULL, claim_token = NULL
        WHERE idempotency_key = 'inbox-replay-001'
        """
    )

    await claim_and_dispatch(conn, {"foundation.test": handler})

    assert len(deliveries) == 1
    inbox = await conn.fetchrow(
        "SELECT status FROM inbox_events WHERE consumer_name = 'worker:foundation.test'"
    )
    assert inbox["status"] == "consumed"


@pytest.mark.asyncio
async def test_non_retryable_handler_dead_letters_event_immediately(conn):
    await conn.execute("DELETE FROM outbox_events")
    await conn.execute(
        """
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'foundation.test', 'terminal-event-001', '{}', 'pending', NOW())
        """
    )

    def malformed_event_handler(_payload):
        raise NonRetryableEventError("malformed payload")

    await claim_and_dispatch(conn, {"foundation.test": malformed_event_handler})

    row = await conn.fetchrow(
        "SELECT status, retry_count, last_error FROM outbox_events WHERE idempotency_key = 'terminal-event-001'"
    )
    assert row["status"] == OUTBOX_DEAD_LETTER
    assert row["retry_count"] == 0
    assert "malformed payload" in row["last_error"]


@pytest.mark.asyncio
async def test_stale_worker_cannot_finalize_new_claim(conn):
    await conn.execute("DELETE FROM outbox_events")
    event = await conn.fetchrow(
        """
        INSERT INTO outbox_events
        (id, event_name, idempotency_key, payload, status, available_at, claimed_at, lease_expires_at, claim_token)
        VALUES
        (gen_random_uuid(), 'foundation.test', 'fenced-claim-001', '{}', 'processing', NOW(), NOW(), NOW() + INTERVAL '15 minutes', gen_random_uuid())
        RETURNING id::text, claim_token::text
        """
    )

    finalized = await _mark_delivered(conn, event["id"], "00000000-0000-0000-0000-000000000000")

    assert finalized is False
    row = await conn.fetchrow(
        "SELECT status, claim_token::text FROM outbox_events WHERE idempotency_key = 'fenced-claim-001'"
    )
    assert row["status"] == OUTBOX_PROCESSING
    assert row["claim_token"] == event["claim_token"]


@pytest.mark.asyncio
async def test_two_workers_cannot_claim_the_same_event(conn):
    await conn.execute("DELETE FROM inbox_events")
    await conn.execute("DELETE FROM outbox_events")
    await conn.execute(
        """
        INSERT INTO outbox_events (id, event_name, idempotency_key, payload, status, available_at)
        VALUES (gen_random_uuid(), 'foundation.test', 'two-workers-001', '{}', 'pending', NOW())
        """
    )
    url = os.getenv("DATABASE_URL", "postgresql://akarai:akarai@postgres:5432/akarai").replace(
        "+asyncpg", ""
    )
    second_conn = await asyncpg.connect(url, statement_cache_size=0)
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_handler(_payload):
        started.set()
        await release.wait()

    first_task = asyncio.create_task(claim_and_dispatch(conn, {"foundation.test": slow_handler}))
    await started.wait()
    second_processed = await claim_and_dispatch(second_conn, {"foundation.test": lambda _: None})
    release.set()
    await first_task
    await second_conn.close()

    assert second_processed is False


@pytest.mark.asyncio
async def test_heartbeat_renews_outbox_and_inbox_leases(conn, monkeypatch):
    import outbox

    await conn.execute("DELETE FROM inbox_events")
    await conn.execute("DELETE FROM outbox_events")
    event = await conn.fetchrow(
        """
        INSERT INTO outbox_events
        (id, event_name, idempotency_key, payload, status, available_at, claimed_at, lease_expires_at, claim_token)
        VALUES (gen_random_uuid(), 'foundation.test', 'heartbeat-001', '{}', 'processing', NOW(), NOW(), NOW() + INTERVAL '1 second', gen_random_uuid())
        RETURNING id::text, claim_token::text
        """
    )
    await conn.execute(
        """
        INSERT INTO inbox_events
        (id, event_id, consumer_name, idempotency_key, status, received_at, lease_expires_at, claim_token, created_at, updated_at)
        VALUES (gen_random_uuid(), $1, 'worker:foundation.test', $2, 'processing', NOW(), NOW() + INTERVAL '1 second', $3::uuid, NOW(), NOW())
        """,
        event["id"],
        f"outbox:{event['id']}",
        event["claim_token"],
    )
    monkeypatch.setattr(outbox, "HEARTBEAT_SECONDS", 0.01)
    monkeypatch.setattr(outbox, "LEASE_SECONDS", 60)
    url = os.getenv("DATABASE_URL", "postgresql://akarai:akarai@postgres:5432/akarai").replace(
        "+asyncpg", ""
    )
    lease_conn = await asyncpg.connect(url, statement_cache_size=0)
    heartbeat = asyncio.create_task(
        _heartbeat_claim(lease_conn, event["id"], event["claim_token"], "worker:foundation.test")
    )
    await asyncio.sleep(0.05)
    heartbeat.cancel()
    with pytest.raises(asyncio.CancelledError):
        await heartbeat
    await lease_conn.close()

    row = await conn.fetchrow(
        "SELECT lease_expires_at > NOW() + INTERVAL '30 seconds' AS outbox_renewed FROM outbox_events WHERE id = $1::uuid",
        event["id"],
    )
    inbox = await conn.fetchrow(
        "SELECT lease_expires_at > NOW() + INTERVAL '30 seconds' AS inbox_renewed FROM inbox_events WHERE event_id = $1",
        event["id"],
    )
    assert row["outbox_renewed"] is True
    assert inbox["inbox_renewed"] is True


@pytest.mark.asyncio
async def test_expired_claim_runs_finalizer_before_dead_letter(conn):
    await conn.execute("DELETE FROM outbox_events")
    await conn.execute(
        """
        INSERT INTO outbox_events
        (id, event_name, idempotency_key, payload, status, available_at, retry_count, max_retries, claimed_at, lease_expires_at, claim_token)
        VALUES (gen_random_uuid(), 'foundation.test', 'expired-finalizer-001', '{"name":"test"}', 'processing', NOW(), 2, 3, NOW() - INTERVAL '20 minutes', NOW() - INTERVAL '5 minutes', gen_random_uuid())
        """
    )
    finalizations = []

    async def finalizer(_conn, payload, event_id, failure):
        finalizations.append((payload, event_id, failure))

    processed = await claim_and_dispatch(
        conn,
        {"foundation.test": lambda _: None},
        dead_letter_handlers={"foundation.test": finalizer},
    )

    assert processed is False
    assert finalizations[0][0] == {"name": "test"}
    assert finalizations[0][2]["retry_count"] == 3
    row = await conn.fetchrow(
        "SELECT status, retry_count FROM outbox_events WHERE idempotency_key = 'expired-finalizer-001'"
    )
    assert row["status"] == OUTBOX_DEAD_LETTER
    assert row["retry_count"] == 3


@pytest.mark.asyncio
async def test_lead_dead_letter_finalizer_marks_pending_results_failed(conn):
    from handlers.leads import finalize_lead_created_dead_letter

    tenant = await conn.fetchval(
        """
        INSERT INTO agency_tenants (id, name, slug, status, created_at, updated_at)
        VALUES (gen_random_uuid(), 'Dead-letter Test Tenant', 'dead-letter-' || gen_random_uuid()::text, 'active', NOW(), NOW())
        RETURNING id::text
        """
    )
    await conn.execute("SELECT set_config('app.tenant_id', $1, false)", tenant)
    listing = await conn.fetchval(
        """
        INSERT INTO listings (id, agency_tenant_id, title, status, created_at, updated_at)
        VALUES (gen_random_uuid(), $1::uuid, 'Dead-letter Test Listing', 'active', NOW(), NOW())
        RETURNING id::text
        """,
        tenant,
    )
    lead = await conn.fetchval(
        """
        INSERT INTO leads (id, agency_tenant_id, listing_id, status, processing_status, created_at, updated_at)
        VALUES (gen_random_uuid(), $1::uuid, $2::uuid, 'new', 'pending_spam', NOW(), NOW())
        RETURNING id::text
        """,
        tenant,
        listing,
    )
    for table in ("lead_spam_results", "lead_level_results"):
        await conn.execute(
            f"""
            INSERT INTO {table} (id, lead_id, agency_tenant_id, status, created_at, updated_at)
            VALUES (gen_random_uuid(), $1::uuid, $2::uuid, 'pending', NOW(), NOW())
            """,
            lead,
            tenant,
        )

    await finalize_lead_created_dead_letter(
        conn,
        {"lead_id": lead, "tenant_id": tenant},
        "event-1",
        {"error": "model unavailable", "retry_count": 3},
    )

    statuses = await conn.fetchrow(
        """
        SELECT l.processing_status,
               (SELECT status FROM lead_spam_results WHERE lead_id = l.id) AS spam_status,
               (SELECT status FROM lead_level_results WHERE lead_id = l.id) AS level_status
        FROM leads AS l
        WHERE l.id = $1::uuid
        """,
        lead,
    )
    assert dict(statuses) == {
        "processing_status": "failed",
        "spam_status": "failed",
        "level_status": "failed",
    }


@pytest.mark.asyncio
async def test_agency_ai_dead_letter_finalizer_marks_job_failed(conn):
    from handlers.agency_ai import finalize_agency_ai_spec_sheet_dead_letter

    job = await conn.fetchval(
        """
        INSERT INTO agency_ai_jobs (id, job_type, status, created_at)
        VALUES (gen_random_uuid(), 'ocr_extraction', 'processing', NOW())
        RETURNING id::text
        """
    )

    await finalize_agency_ai_spec_sheet_dead_letter(
        conn,
        {"job_id": job},
        "event-2",
        {"error": "OCR unavailable", "retry_count": 3},
    )

    row = await conn.fetchrow(
        "SELECT status, error_message, completed_at FROM agency_ai_jobs WHERE id = $1::uuid", job
    )
    assert row["status"] == "failed"
    assert row["error_message"] == "OCR unavailable"
    assert row["completed_at"] is not None
