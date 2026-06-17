"""Unit tests for lead analytics — trend aggregation and review-rate summaries."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.leads.schemas import LeadProcessingSummary, LeadProcessingTrendsResponse


class TestLeadProcessingSummary:
    def test_summary_defaults(self):
        s = LeadProcessingSummary()
        assert s.total_leads == 0
        assert s.spam_count == 0
        assert s.hot_count == 0
        assert s.reviewed_count == 0

    def test_summary_computes_ratios(self):
        s = LeadProcessingSummary(
            total_leads=100,
            spam_count=20,
            not_spam_count=80,
            hot_count=40,
            normal_count=40,
            pending_count=5,
            reviewed_count=60,
        )
        assert s.spam_count == 20
        assert s.hot_count == 40
        assert s.reviewed_count == 60


class TestTrendsResponse:
    def test_trends_with_rates(self):
        summary = LeadProcessingSummary(
            total_leads=100,
            spam_count=15,
            not_spam_count=85,
            hot_count=50,
            normal_count=35,
            pending_count=3,
            reviewed_count=70,
        )
        tenant_id = uuid4()
        trends = LeadProcessingTrendsResponse(
            tenant_id=tenant_id,
            summary=summary,
            spam_rate=0.15,
            hot_rate=0.588,
            review_rate=0.70,
            fallback_count=2,
        )
        assert trends.spam_rate == 0.15
        assert trends.hot_rate == 0.588
        assert trends.review_rate == 0.70
        assert trends.fallback_count == 2

    def test_trends_with_zero_leads(self):
        summary = LeadProcessingSummary()
        tenant_id = uuid4()
        trends = LeadProcessingTrendsResponse(
            tenant_id=tenant_id,
            summary=summary,
            spam_rate=0.0,
            hot_rate=0.0,
            review_rate=0.0,
            fallback_count=0,
        )
        assert trends.spam_rate == 0.0
        assert trends.hot_rate == 0.0


class TestQueryServiceExistence:
    def test_query_service_exists(self):
        from app.leads.query_service import LeadProcessingQueryService
        assert LeadProcessingQueryService is not None

    def test_query_service_has_trend_summary(self):
        from app.leads.query_service import LeadProcessingQueryService
        assert hasattr(LeadProcessingQueryService, "get_trend_summary")
        assert callable(LeadProcessingQueryService.get_trend_summary)

    def test_query_service_has_summary(self):
        from app.leads.query_service import LeadProcessingQueryService
        assert hasattr(LeadProcessingQueryService, "get_lead_processing_summary")
        assert callable(LeadProcessingQueryService.get_lead_processing_summary)
