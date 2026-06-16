"""Unit tests for assistant tool orchestration in the RAG chat service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.rag.service import (
    _detect_tool_intent,
    _format_lead_summary,
    _format_listing_summary,
)


class TestDetectToolIntent:
    def test_detects_list_recent_leads(self):
        assert _detect_tool_intent("Show me the last 5 leads") == "list_recent_leads"

    def test_detects_list_recent_leads_recently(self):
        assert _detect_tool_intent("Can I see the recent leads please?") == "list_recent_leads"

    def test_detects_search_listings(self):
        assert _detect_tool_intent("Help me search listings in Beirut") == "search_listings"

    def test_detects_find_listing(self):
        assert _detect_tool_intent("Find listing 12") == "search_listings"

    def test_detects_leads_by_date(self):
        assert _detect_tool_intent("Leads from last week") == "list_leads_by_date"
        assert _detect_tool_intent("Leads between Monday and Friday") == "list_leads_by_date"
        assert _detect_tool_intent("Leads of October") == "list_leads_by_date"
        assert _detect_tool_intent("Leads on 2025-01-15") == "list_leads_by_date"

    def test_returns_none_for_policy_question(self):
        assert _detect_tool_intent("What is the parking policy?") is None
        assert _detect_tool_intent("What is the visitor rule?") is None

    def test_returns_none_for_unknown(self):
        assert _detect_tool_intent("hello world") is None
        assert _detect_tool_intent("") is None

    def test_case_insensitive(self):
        assert _detect_tool_intent("SHOW ME THE LAST 5 LEADS") == "list_recent_leads"

    def test_policy_question_with_id_phrase_does_not_route_to_tool(self):
        # The "leads" word alone should not trigger — it must be a
        # directional phrase like "leads of/between/from/on".
        assert _detect_tool_intent("lead id 12345") is None


class TestFormatLeadSummary:
    def test_includes_name_status_email_phone(self):
        lead = MagicMock()
        lead.name = "Layla"
        lead.email = "layla@example.com"
        lead.phone = "+9613123456"
        lead.status = "new"
        out = _format_lead_summary(lead)
        assert "Layla" in out
        assert "new" in out
        assert "layla@example.com" in out
        assert "+9613123456" in out

    def test_handles_missing_fields(self):
        lead = MagicMock()
        lead.name = None
        lead.email = None
        lead.phone = None
        lead.status = None
        out = _format_lead_summary(lead)
        assert "Unnamed" in out
        assert "—" in out
        assert "new" in out


class TestFormatListingSummary:
    def test_includes_title_status_city(self):
        listing = MagicMock()
        listing.title = "Spacious 3BR"
        listing.status = "published"
        listing.city = "Beirut"
        listing.bedrooms = 3
        listing.area_size = "150"
        listing.area_unit = "sqm"
        out = _format_listing_summary(listing)
        assert "Spacious 3BR" in out
        assert "published" in out
        assert "Beirut" in out
        assert "3" in out

    def test_handles_missing_optional(self):
        listing = MagicMock()
        listing.title = "Studio"
        listing.status = "draft"
        listing.city = None
        listing.bedrooms = None
        listing.area_size = None
        listing.area_unit = None
        out = _format_listing_summary(listing)
        assert "Studio" in out
        assert "draft" in out
        assert "—" in out
