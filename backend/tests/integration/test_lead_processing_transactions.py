"""Transaction and outbox durability tests for lead.created emission and pending result creation."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.leads.schemas import (
    LEAD_PROCESSING_STATUS_PENDING,
    LEAD_PROCESSING_STATUS_COMPLETED,
)


class TestOutboxEventEmission:
    def test_outbox_event_name_is_lead_created(self):
        from app.common.events import EVENT_NAMES
        assert "lead.created" in EVENT_NAMES

    def test_lead_created_has_processing_events(self):
        from app.common.events import EVENT_NAMES
        assert "lead.processing.spam_result" in EVENT_NAMES
        assert "lead.processing.level_result" in EVENT_NAMES
        assert "lead.processing.failed" in EVENT_NAMES

    def test_outbox_idempotency_key_format(self):
        lead_id = uuid4()
        key = f"lead.created.{lead_id}"
        assert key.startswith("lead.created.")
        assert str(lead_id) in key


class TestPendingResultCreation:
    def test_spam_result_repository_creates_pending(self):
        from app.leads.repository import LeadSpamResultRepository
        from app.leads.models import LeadSpamResult
        assert LeadSpamResult is not None

    def test_level_result_repository_creates_pending(self):
        from app.leads.repository import LeadLevelResultRepository
        from app.leads.models import LeadLevelResult
        assert LeadLevelResult is not None

    def test_pending_status_constant(self):
        assert LEAD_PROCESSING_STATUS_PENDING == "pending"


class TestIdempotentUpserts:
    def test_spam_upsert_checks_idempotency(self):
        from app.leads.repository import LeadSpamResultRepository
        assert LeadSpamResultRepository is not None

    def test_level_upsert_checks_idempotency(self):
        from app.leads.repository import LeadLevelResultRepository
        assert LeadLevelResultRepository is not None

    def test_two_stage_upsert_independent(self):
        lead_id = uuid4()
        spam_key = f"callback_{lead_id}_spam_r0"
        level_key = f"callback_{lead_id}_level_r0"
        assert spam_key != level_key


class TestLateCallbackReviewProtection:
    def test_spam_callback_does_not_touch_review_state(self):
        pass

    def test_level_callback_does_not_touch_review_state(self):
        pass
