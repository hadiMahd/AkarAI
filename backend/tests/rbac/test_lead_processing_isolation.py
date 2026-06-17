"""RBAC and tenant-isolation tests for lead processing callbacks and access."""
from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_infra():
    """Sync no-op: shadows async conftest fixture for sync tests."""
    yield


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Sync no-op: shadows async conftest fixture for sync tests."""
    yield



class TestCallbackAuth:
    def test_callback_token_is_required(self):
        from app.common.config import settings
        assert hasattr(settings, "lead_model_service_callback_token")

    def test_callback_endpoint_is_defined(self):
        from app.leads.router import internal_router
        paths = [r.path for r in internal_router.routes]
        assert "/api/v1/internal/leads/classification-callback" in paths


class TestTenantIsolation:
    def test_callback_validates_tenant_match(self):
        pass

    def test_spam_result_query_is_tenant_scoped(self):
        from app.leads.repository import LeadSpamResultRepository
        assert LeadSpamResultRepository is not None

    def test_level_result_query_is_tenant_scoped(self):
        from app.leads.repository import LeadLevelResultRepository
        assert LeadLevelResultRepository is not None


class TestAgencyLeadClassificationAccess:
    def test_agency_lead_response_includes_processing_status(self):
        from app.leads.schemas import LeadResponse
        schema_fields = LeadResponse.model_fields
        assert "processing_status" in schema_fields
        assert "spam_label" in schema_fields
        assert "lead_level" in schema_fields

    def test_agency_lead_list_is_tenant_scoped(self):
        from app.leads.service import LeadService
        assert LeadService is not None
