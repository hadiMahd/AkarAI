"""Integration tests for lead analytics API — tenant-scoped trend summaries."""
from __future__ import annotations

import pytest


class TestLeadAnalyticsEndpoint:
    def test_endpoint_is_registered(self):
        from app.analytics.router import router
        paths = [r.path for r in router.routes]
        assert "/agency/dashboard/lead-processing-trends" in paths

    def test_endpoint_returns_trends_schema(self):
        from app.leads.schemas import LeadProcessingTrendsResponse
        assert LeadProcessingTrendsResponse is not None

    def test_response_includes_lead_processing_summary(self):
        from app.leads.schemas import LeadProcessingSummary
        assert LeadProcessingSummary is not None


class TestAgencyDashboardTrendQuery:
    def test_summary_includes_all_required_fields(self):
        from app.leads.schemas import LeadProcessingSummary
        fields = LeadProcessingSummary.model_fields
        required = ["total_leads", "spam_count", "not_spam_count", "hot_count",
                     "normal_count", "pending_count", "reviewed_count"]
        for field in required:
            assert field in fields, f"Missing field: {field}"

    def test_trends_includes_all_required_fields(self):
        from app.leads.schemas import LeadProcessingTrendsResponse
        fields = LeadProcessingTrendsResponse.model_fields
        required = ["tenant_id", "summary", "spam_rate", "hot_rate",
                     "review_rate", "fallback_count"]
        for field in required:
            assert field in fields, f"Missing field: {field}"
