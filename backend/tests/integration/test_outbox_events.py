import uuid

import pytest
from sqlalchemy import select, text

from app.common.database import async_session_factory
from app.common.events import (
    OUTBOX_DEAD_LETTER,
    OUTBOX_DELIVERED,
    OUTBOX_FAILED,
    OUTBOX_PENDING,
    OUTBOX_PROCESSING,
    OutboxEvent,
    publish_outbox_event,
)


@pytest.mark.anyio
class TestOutboxEvents:
    @pytest.mark.integration
    async def test_publish_outbox_event(self):
        key = f"test-outbox-{uuid.uuid4()}"
        event = await publish_outbox_event(
            event_name="lead.created",
            payload={"test": True},
            idempotency_key=key,
        )
        assert event.status == OUTBOX_PENDING
        assert event.event_name == "lead.created"

    @pytest.mark.integration
    async def test_idempotency_key_uniqueness(self):
        key = f"test-idem-{uuid.uuid4()}"
        await publish_outbox_event("lead.created", {"a": 1}, idempotency_key=key)
        with pytest.raises(Exception):
            await publish_outbox_event("lead.created", {"a": 2}, idempotency_key=key)

    @pytest.mark.integration
    async def test_status_lifecycle(self):
        key = f"test-lifecycle-{uuid.uuid4()}"
        event = await publish_outbox_event("viewing.scheduled", {}, idempotency_key=key)

        async with async_session_factory() as session:
            result = await session.execute(
                select(OutboxEvent).where(OutboxEvent.idempotency_key == key)
            )
            evt = result.scalar_one()
            evt.status = OUTBOX_PROCESSING
            await session.commit()

        async with async_session_factory() as session:
            result = await session.execute(
                select(OutboxEvent).where(OutboxEvent.idempotency_key == key)
            )
            evt = result.scalar_one()
            evt.status = OUTBOX_DELIVERED
            await session.commit()

        async with async_session_factory() as session:
            result = await session.execute(
                select(OutboxEvent).where(OutboxEvent.idempotency_key == key)
            )
            evt = result.scalar_one()
            assert evt.status == OUTBOX_DELIVERED
