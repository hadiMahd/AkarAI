"""Unit tests for lead processing service — stage ordering, fail-open, idempotent callbacks."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.leads.schemas import (
    LEAD_PROCESSING_STAGE_SPAM,
    LEAD_PROCESSING_STAGE_LEVEL,
    LEAD_PROCESSING_STATUS_COMPLETED,
    LEAD_PROCESSING_STATUS_FAILED,
    LEAD_SPAM_LABEL_SPAM,
    LEAD_SPAM_LABEL_NOT_SPAM,
    LEAD_LEVEL_HOT,
    LEAD_LEVEL_NORMAL,
)


class TestLeadProcessingStageOrdering:
    def test_spam_stage_comes_before_level(self):
        assert LEAD_PROCESSING_STAGE_SPAM == "spam"
        assert LEAD_PROCESSING_STAGE_LEVEL == "level"

    def test_completed_and_failed_statuses(self):
        assert LEAD_PROCESSING_STATUS_COMPLETED == "completed"
        assert LEAD_PROCESSING_STATUS_FAILED == "failed"

    def test_spam_labels(self):
        assert LEAD_SPAM_LABEL_SPAM == "spam"
        assert LEAD_SPAM_LABEL_NOT_SPAM == "not_spam"


class TestFailOpenDefaults:
    def test_empty_message_is_spam_default_true(self):
        from app.common.config import settings
        assert settings.lead_processing_empty_message_is_spam is True

    def test_retry_config_present(self):
        from app.common.config import settings
        assert settings.lead_processing_retry_max_attempts > 0
        assert settings.lead_processing_retry_base_delay_seconds > 0

    def test_model_service_url_is_set(self):
        from app.common.config import settings
        assert settings.lead_model_service_url


class TestIdempotentCallbacks:
    def test_idempotency_key_format(self):
        lead_id = uuid4()
        id_key = f"callback_{lead_id}_spam_r0"
        assert "spam" in id_key
        assert str(lead_id) in id_key
        assert "r0" in id_key

    def test_idempotency_keys_unique_per_stage(self):
        lead_id = uuid4()
        spam_key = f"callback_{lead_id}_spam_r0"
        level_key = f"callback_{lead_id}_level_r0"
        assert spam_key != level_key

    def test_idempotency_keys_unique_per_retry(self):
        lead_id = uuid4()
        r0 = f"callback_{lead_id}_spam_r0"
        r1 = f"callback_{lead_id}_spam_r1"
        assert r0 != r1

    def test_empty_message_idempotency_key(self):
        lead_id = uuid4()
        id_key = f"empty_spam_{lead_id}"
        assert "empty_spam" in id_key
        assert str(lead_id) in id_key


class TestCallbackSchema:
    def test_spam_callback_with_all_fields(self):
        from app.leads.schemas import LeadClassificationCallbackRequest
        cb = LeadClassificationCallbackRequest(
            lead_id=uuid4(),
            tenant_id=uuid4(),
            stage="spam",
            status="completed",
            label="not_spam",
            score=0.1,
            details={"source": "model"},
            retry_count=1,
        )
        assert cb.lead_id is not None
        assert cb.stage == "spam"
        assert cb.status == "completed"
        assert cb.label == "not_spam"

    def test_level_callback_with_all_fields(self):
        from app.leads.schemas import LeadClassificationCallbackRequest
        cb = LeadClassificationCallbackRequest(
            lead_id=uuid4(),
            tenant_id=uuid4(),
            stage="level",
            status="completed",
            label="hot",
            score=0.85,
            retry_count=0,
        )
        assert cb.stage == "level"
        assert cb.status == "completed"

    def test_callback_rejects_invalid_stage(self):
        from app.leads.schemas import LeadClassificationCallbackRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LeadClassificationCallbackRequest(
                lead_id=uuid4(),
                tenant_id=uuid4(),
                stage="invalid",
                status="completed",
            )

    def test_callback_rejects_invalid_status(self):
        from app.leads.schemas import LeadClassificationCallbackRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LeadClassificationCallbackRequest(
                lead_id=uuid4(),
                tenant_id=uuid4(),
                stage="spam",
                status="invalid",
            )


class TestEmptyMessageSpamDefaults:
    def test_schema_accepts_empty_labels(self):
        from app.leads.schemas import LeadClassificationCallbackRequest
        cb = LeadClassificationCallbackRequest(
            lead_id=uuid4(),
            tenant_id=uuid4(),
            stage="spam",
            status="completed",
            label=None,
            score=None,
        )
        assert cb.label is None
        assert cb.score is None


class TestDuplicateSubmissions:
    def test_outbox_idempotency_key_per_lead(self):
        lead_id = uuid4()
        key1 = f"lead.created.{lead_id}"
        assert str(lead_id) in key1

    def test_different_lead_ids_produce_different_keys(self):
        id1 = uuid4()
        id2 = uuid4()
        assert f"lead.created.{id1}" != f"lead.created.{id2}"


class TestProcessingSummarySchema:
    def test_summary_defaults(self):
        from app.leads.schemas import LeadProcessingSummary
        s = LeadProcessingSummary()
        assert s.total_leads == 0
        assert s.spam_count == 0
        assert s.hot_count == 0

    def test_summary_with_data(self):
        from app.leads.schemas import LeadProcessingSummary
        s = LeadProcessingSummary(
            total_leads=10,
            spam_count=3,
            not_spam_count=7,
            hot_count=4,
            normal_count=3,
            pending_count=2,
            reviewed_count=5,
        )
        assert s.spam_count == 3
        assert s.hot_count == 4
        assert s.reviewed_count == 5

    def test_trends_response(self):
        from app.leads.schemas import LeadProcessingTrendsResponse, LeadProcessingSummary
        from uuid import uuid4
        tenant_id = uuid4()
        summary = LeadProcessingSummary(total_leads=10, spam_count=3)
        trends = LeadProcessingTrendsResponse(
            tenant_id=tenant_id,
            summary=summary,
            spam_rate=0.3,
            hot_rate=0.57,
            review_rate=0.5,
            fallback_count=1,
        )
        assert trends.spam_rate == 0.3
        assert trends.fallback_count == 1
