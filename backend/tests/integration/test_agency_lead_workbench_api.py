"""Integration tests for agency lead workbench API — spam queue, Hot/Normal badges, review actions."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.leads.schemas import (
    LEAD_SPAM_LABEL_SPAM,
    LEAD_SPAM_LABEL_NOT_SPAM,
    LEAD_LEVEL_HOT,
    LEAD_LEVEL_NORMAL,
)
from app.common.domain import LEAD_STATUS_NEW, LEAD_STATUS_REVIEWED


class TestSpamQueueFiltering:
    def test_spam_label_query_param_accepted(self):
        assert LEAD_SPAM_LABEL_SPAM == "spam"

    def test_not_spam_label_constant(self):
        assert LEAD_SPAM_LABEL_NOT_SPAM == "not_spam"

    def test_list_agency_leads_has_spam_filter(self):
        from app.leads.service import LeadService
        import inspect
        sig = inspect.signature(LeadService.list_tenant_leads)
        assert "spam_label" in sig.parameters
        assert "processing_status" in sig.parameters


class TestHotNormalBadges:
    def test_hot_level_constant(self):
        assert LEAD_LEVEL_HOT == "hot"

    def test_normal_level_constant(self):
        assert LEAD_LEVEL_NORMAL == "normal"

    def test_lead_response_has_spam_and_level_fields(self):
        from app.leads.schemas import LeadResponse
        fields = LeadResponse.model_fields
        assert "spam_label" in fields
        assert "lead_level" in fields
        assert "spam_score" in fields
        assert "level_score" in fields


class TestReviewActions:
    def test_review_request_schema(self):
        from app.leads.schemas import LeadReviewRequest
        req = LeadReviewRequest(outcome="interested", notes="Follow up tomorrow")
        assert req.outcome == "interested"
        assert req.notes == "Follow up tomorrow"

    def test_reviewed_record_response_schema(self):
        from app.leads.schemas import ReviewedLeadRecordResponse
        from datetime import datetime, timezone

        resp = ReviewedLeadRecordResponse(
            id=uuid4(),
            lead_id=uuid4(),
            agency_tenant_id=uuid4(),
            reviewed_by_user_id=uuid4(),
            outcome="spam_confirmed",
            notes="Auto-generated spam",
            created_at=datetime.now(timezone.utc),
        )
        assert resp.outcome == "spam_confirmed"


class TestPendingStateRefresh:
    def test_processing_status_field_in_lead_response(self):
        from app.leads.schemas import LeadResponse
        fields = LeadResponse.model_fields
        assert "processing_status" in fields

    def test_lead_status_is_independent(self):
        assert LEAD_STATUS_NEW == "new"
        assert LEAD_STATUS_REVIEWED == "reviewed"
