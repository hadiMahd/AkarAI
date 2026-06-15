import uuid

import pytest
from sqlalchemy import select

from app.common.database import async_session_factory
from app.common.events import INBOX_CONSUMED, InboxEvent, record_inbox_event


@pytest.mark.anyio
class TestInboxEvents:
    @pytest.mark.integration
    async def test_record_inbox_event(self):
        key = f"test-inbox-{uuid.uuid4()}"
        event = await record_inbox_event(
            event_id="evt-1",
            consumer_name="test-consumer",
            idempotency_key=key,
        )
        assert event.status == "processing"

    @pytest.mark.integration
    async def test_duplicate_consumption_prevention(self):
        key = f"test-inbox-dup-{uuid.uuid4()}"
        await record_inbox_event("evt-2", "test-consumer", idempotency_key=key)
        with pytest.raises(Exception):
            await record_inbox_event("evt-2", "test-consumer", idempotency_key=key)
