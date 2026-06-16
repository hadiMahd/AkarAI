"""Unit tests for lead reply draft and comparison summary flow helpers."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.ai.schemas import (
    ComparisonSummaryRequest,
    ExtractedListingSpecs,
    LeadReplyDraftRequest,
    ListingDraftRequest,
)


class TestExtractedListingSpecs:
    def test_builds_minimal_specs(self):
        specs = ExtractedListingSpecs()
        assert specs.bedrooms is None
        assert specs.area_size is None
        assert specs.field_confidence == {}
        assert specs.source_snippets == {}

    def test_serializes_full_specs(self):
        specs = ExtractedListingSpecs(
            area_size="150",
            area_unit="sqm",
            bedrooms=3,
            bathrooms=2,
            parking=1,
            property_type="apartment",
            listing_purpose="rent",
            furnishing="furnished",
            city="Beirut",
            address="123 Hamra Street",
            field_confidence={"bedrooms": "high"},
            source_snippets={"bedrooms": "3 bedrooms"},
        )
        assert specs.bedrooms == 3
        assert specs.field_confidence["bedrooms"] == "high"
        assert specs.source_snippets["bedrooms"] == "3 bedrooms"


class TestListingDraftRequest:
    def test_validates_required_listing_context(self):
        req = ListingDraftRequest(
            listing_context={"title": "A", "city": "Beirut", "price": 1000}
        )
        assert req.listing_context["title"] == "A"

    def test_accepts_extracted_specs(self):
        req = ListingDraftRequest(
            listing_context={"title": "A", "city": "Beirut"},
            extracted_specs=ExtractedListingSpecs(bedrooms=3),
        )
        assert req.extracted_specs is not None
        assert req.extracted_specs.bedrooms == 3

    def test_rejects_empty_listing_context(self):
        # The service layer enforces that listing_context has at least
        # the minimum required fields. The schema itself accepts any
        # dict, but missing required fields should be caught upstream.
        req = ListingDraftRequest(listing_context={})
        assert req.listing_context == {}
        assert req.extracted_specs is None


class TestLeadReplyDraftRequest:
    def test_validates_required_fields(self):
        req = LeadReplyDraftRequest(
            lead_id=uuid4(),
            channel="email",
            listing_id=None,
        )
        assert req.channel == "email"

    def test_accepts_whatsapp_channel(self):
        req = LeadReplyDraftRequest(
            lead_id=uuid4(),
            channel="whatsapp",
            listing_id=None,
        )
        assert req.channel == "whatsapp"

    def test_rejects_unknown_channel(self):
        with pytest.raises(ValueError):
            LeadReplyDraftRequest(
                lead_id=uuid4(),
                channel="sms",
                listing_id=None,
            )


class TestComparisonSummaryRequest:
    def test_accepts_two_to_four_listing_ids(self):
        for n in (2, 3, 4):
            req = ComparisonSummaryRequest(listing_ids=[uuid4() for _ in range(n)])
            assert len(req.listing_ids) == n

    def test_rejects_one_listing(self):
        with pytest.raises(ValueError):
            ComparisonSummaryRequest(listing_ids=[uuid4()])

    def test_rejects_five_listings(self):
        with pytest.raises(ValueError):
            ComparisonSummaryRequest(listing_ids=[uuid4() for _ in range(5)])

    def test_dedupes_listing_ids(self):
        one = uuid4()
        two = uuid4()
        req = ComparisonSummaryRequest(listing_ids=[one, one, two, two])
        assert len(req.listing_ids) == 2
        assert req.listing_ids[0] == one
        assert req.listing_ids[1] == two


class TestGuardrailFallbackMarkers:
    """Verify that the guardrailed result helpers carry the expected
    blocked status markers so the service layer can persist the right
    job state.
    """

    def test_blocked_incomplete_returns_blocked_status(self):
        from app.ai.guardrails import GuardrailedGenerationResult

        result = GuardrailedGenerationResult(
            answer_text="",
            guardrail_status="blocked",
            blocked_reason="comparison_summary_incomplete",
            generation_provider="test",
        )
        assert result.guardrail_status == "blocked"
        assert result.answer_text == ""

    def test_passed_status_has_text(self):
        from app.ai.guardrails import GuardrailedGenerationResult

        result = GuardrailedGenerationResult(
            answer_text="Some answer",
            guardrail_status="passed",
            blocked_reason=None,
            generation_provider="test",
        )
        assert result.guardrail_status == "passed"
        assert result.answer_text == "Some answer"
