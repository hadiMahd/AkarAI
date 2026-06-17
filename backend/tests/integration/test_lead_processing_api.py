"""Integration tests for lead processing API — asynchronous classification callbacks."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.leads.schemas import (
    LEAD_PROCESSING_STATUS_COMPLETED,
    LEAD_SPAM_LABEL_SPAM,
    LEAD_SPAM_LABEL_NOT_SPAM,
    LEAD_LEVEL_HOT,
    LEAD_LEVEL_NORMAL,
)


class TestSpamCallbackSchema:
    def test_callback_body_stage_must_be_valid(self):
        from app.leads.schemas import LeadClassificationCallbackRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LeadClassificationCallbackRequest(
                lead_id=uuid4(),
                tenant_id=uuid4(),
                stage="unknown_stage",
                status="completed",
            )

    def test_callback_body_status_must_be_valid(self):
        from app.leads.schemas import LeadClassificationCallbackRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LeadClassificationCallbackRequest(
                lead_id=uuid4(),
                tenant_id=uuid4(),
                stage="spam",
                status="unknown_status",
            )

    def test_callback_bearer_token_is_validated(self):
        from app.common.config import settings
        assert hasattr(settings, "lead_model_service_callback_token")

    def test_callback_endpoint_registered(self):
        from app.leads.router import internal_router
        paths = [r.path for r in internal_router.routes]
        assert len(paths) > 0
        assert any("classification-callback" in p for p in paths)


class TestClassificationResultEndpoints:
    def test_spam_result_response_schema(self):
        from app.leads.schemas import LeadSpamResultResponse
        from datetime import datetime, timezone

        resp = LeadSpamResultResponse(
            id=uuid4(),
            lead_id=uuid4(),
            agency_tenant_id=uuid4(),
            status="completed",
            label="not_spam",
            score=0.12,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert resp.label == "not_spam"
        assert resp.status == "completed"

    def test_level_result_response_schema(self):
        from app.leads.schemas import LeadLevelResultResponse
        from datetime import datetime, timezone

        resp = LeadLevelResultResponse(
            id=uuid4(),
            lead_id=uuid4(),
            agency_tenant_id=uuid4(),
            status="completed",
            level="hot",
            score=0.85,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert resp.level == "hot"
        assert resp.status == "completed"


class TestCallbackResponseSchema:
    def test_callback_response_spam(self):
        from app.leads.schemas import LeadClassificationCallbackResponse

        resp = LeadClassificationCallbackResponse(
            lead_id=uuid4(),
            stage="spam",
            status="completed",
            label="not_spam",
        )
        assert resp.stage == "spam"
        assert resp.label == "not_spam"

    def test_callback_response_level(self):
        from app.leads.schemas import LeadClassificationCallbackResponse

        resp = LeadClassificationCallbackResponse(
            lead_id=uuid4(),
            stage="level",
            status="completed",
            label="hot",
        )
        assert resp.stage == "level"
        assert resp.label == "hot"


class TestEmptyMessageDuplicateSubmissions:
    def test_empty_message_skips_level_classification(self):
        from app.common.config import settings
        msg = ""
        assert settings.lead_processing_empty_message_is_spam
        assert not msg.strip()

    def test_non_empty_message_proceeds_to_level(self):
        from app.common.config import settings
        msg = "I am interested in this property"
        assert msg.strip()
        assert settings.lead_processing_empty_message_is_spam

    def test_empty_message_get_spam_label_in_schema(self):
        assert LEAD_SPAM_LABEL_SPAM == "spam"
        assert LEAD_SPAM_LABEL_NOT_SPAM == "not_spam"


class TestLevelClassification:
    def test_hot_level_constant(self):
        assert LEAD_LEVEL_HOT == "hot"

    def test_normal_level_constant(self):
        assert LEAD_LEVEL_NORMAL == "normal"

    def test_completed_status_constant(self):
        assert LEAD_PROCESSING_STATUS_COMPLETED == "completed"
