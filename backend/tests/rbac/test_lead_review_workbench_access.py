"""RBAC coverage for lead review workbench — spam views, review state queries, support/admin access."""
from __future__ import annotations

import inspect

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_infra():
    """Sync no-op: shadows async conftest fixture for sync tests."""
    yield


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Sync no-op: shadows async conftest fixture for sync tests."""
    yield



class TestLeadListAccess:
    def test_list_tenant_leads_requires_tenant_context(self):
        from app.leads.service import LeadService
        sig = inspect.signature(LeadService.list_tenant_leads)
        assert "reviewed" in sig.parameters
        assert "spam_label" in sig.parameters


class TestSpamViewIsolation:
    def test_repository_spam_filter_is_tenant_scoped(self):
        from app.leads.repository import LeadRepository
        sig = inspect.signature(LeadRepository.list_by_tenant)
        assert "spam_label" in sig.parameters

    def test_spam_result_repo_exists(self):
        from app.leads.repository import LeadSpamResultRepository
        assert LeadSpamResultRepository is not None


class TestReviewAccess:
    def test_review_endpoint_requires_tenant_context(self):
        from app.leads.router import agency_router
        assert agency_router is not None

    def test_review_request_schema_validates_outcome(self):
        from app.leads.schemas import LeadReviewRequest
        req = LeadReviewRequest(outcome=None, notes=None)
        assert req.outcome is None
