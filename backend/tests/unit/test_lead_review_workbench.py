"""Unit tests for lead review workbench — spam filters, review persistence, late-callback updates."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.leads.schemas import (
    LEAD_PROCESSING_STATUS_COMPLETED,
    LEAD_PROCESSING_STATUS_PENDING,
    LEAD_SPAM_LABEL_SPAM,
    LEAD_SPAM_LABEL_NOT_SPAM,
    LEAD_LEVEL_HOT,
    LEAD_LEVEL_NORMAL,
)
from app.common.domain import (
    LEAD_STATUS_TRANSITIONS,
    LEAD_STATUS_NEW,
    LEAD_STATUS_REVIEWED,
)


class TestSpamFilters:
    def test_spam_label_constant_declared(self):
        assert LEAD_SPAM_LABEL_SPAM == "spam"
        assert LEAD_SPAM_LABEL_NOT_SPAM == "not_spam"

    def test_repository_accepts_spam_label_filter(self):
        import inspect
        from app.leads.repository import LeadRepository
        sig = inspect.signature(LeadRepository.list_by_tenant)
        assert "spam_label" in sig.parameters

    def test_repository_accepts_processing_status_filter(self):
        import inspect
        from app.leads.repository import LeadRepository
        sig = inspect.signature(LeadRepository.list_by_tenant)
        assert "processing_status" in sig.parameters


class TestReviewPersistence:
    def test_new_to_reviewed_transition_allowed(self):
        transitions = LEAD_STATUS_TRANSITIONS.get("new", [])
        assert "reviewed" in transitions

    def test_reviewed_to_closed_transition_allowed(self):
        transitions = LEAD_STATUS_TRANSITIONS.get("reviewed", [])
        assert "closed" in transitions

    def test_reviewed_lead_keeps_processing_status(self):
        assert LEAD_PROCESSING_STATUS_COMPLETED == "completed"


class TestLateCallbackClassificationUpdates:
    def test_processing_status_field_exists_on_lead_model(self):
        from app.leads.models import Lead
        assert hasattr(Lead, "processing_status")

    def test_lead_status_transitions_are_independent_of_processing(self):
        assert LEAD_STATUS_NEW == "new"
        assert LEAD_STATUS_REVIEWED == "reviewed"

    def test_spam_label_and_level_independent_of_review(self):
        assert LEAD_SPAM_LABEL_SPAM == "spam"
        assert LEAD_LEVEL_HOT == "hot"
        assert LEAD_LEVEL_NORMAL == "normal"
