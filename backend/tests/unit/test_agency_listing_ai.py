"""Unit tests for agency listing AI: OCR spec extraction heuristics, job state
transitions, and listing draft generation without a database."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.ai.jobs import (
    JOB_STATUS_BLOCKED,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_PROCESSING,
    JOB_STATUS_QUEUED,
    JOB_TYPE_LISTING_DRAFT,
    JOB_TYPE_OCR_EXTRACTION,
    mark_completed,
    mark_failed,
    mark_processing,
    new_job,
)
from app.ai.ocr import extract_listing_specs, extract_listing_specs_via_llm
from app.ai.schemas import ExtractedListingSpecs
from app.ai.models import AgencyAIJob
from app.ai.service import (
    AgencyAIService,
    _validate_ocr_upload,
    _parse_json_object,
    _public_listing_snapshot,
)


# Note: this is a pure-Python test file; we do not patch async DB
# operations so we don't trigger the redis-dependent conftest fixtures.


pytestmark = pytest.mark.anyio


# ── OCR spec extraction heuristics ──────────────────────────────────────────


class TestExtractListingSpecs:
    def test_extracts_bedrooms_bathrooms_area_city(self):
        result = extract_listing_specs(
            "3 bedrooms, 2 bathrooms, 150 sqm apartment in Beirut for rent"
        )
        assert result["bedrooms"] == 3
        assert result["bathrooms"] == 2
        assert result["area_size"] == Decimal("150")
        assert result["area_unit"] == "sqm"
        assert result["city"] == "Beirut"
        assert result["property_type"] == "apartment"
        assert result["listing_purpose"] == "rent"
        assert result["field_confidence"]["bedrooms"] == "high"
        assert result["field_confidence"]["area_size"] == "high"

    def test_extracts_villa_with_sqft_and_floor(self):
        result = extract_listing_specs(
            "Villa for sale, 4 bedrooms, 3 bathrooms, 2500 sqft, "
            "floor 2, fully furnished"
        )
        assert result["bedrooms"] == 4
        assert result["bathrooms"] == 3
        assert result["area_size"] == Decimal("2500")
        assert result["area_unit"] == "sqft"
        assert result["floor"] == 2
        assert result["property_type"] == "villa"
        assert result["listing_purpose"] == "sale"
        assert result["furnishing"] == "furnished"

    def test_extracts_address(self):
        result = extract_listing_specs(
            "Apartment in Beirut, 2 bedrooms, 1 bathroom, 80 sqm, "
            "address: 123 Hamra Street"
        )
        assert result["address"] == "123 Hamra Street"
        assert result["bedrooms"] == 2
        assert result["source_snippets"]["address"].lower().startswith("address")

    def test_extracts_parking(self):
        result = extract_listing_specs(
            "Apartment with 1 parking, 3 bedrooms, 2 bathrooms"
        )
        assert result["parking"] == 1
        assert result["source_snippets"]["parking"] == "1 parking"

    def test_empty_text_returns_excerpt_and_empty_confidence(self):
        result = extract_listing_specs("")
        assert result["raw_text_excerpt"] == ""
        assert result["field_confidence"] == {}
        assert result["source_snippets"] == {}

    def test_no_matches_returns_only_excerpt(self):
        result = extract_listing_specs("Hello world, this is a test of OCR.")
        assert "raw_text_excerpt" in result
        assert result.get("bedrooms") is None
        assert result.get("area_size") is None
        assert result["field_confidence"] == {}

    def test_area_unit_m2_normalized_to_sqm(self):
        result = extract_listing_specs("Studio 45 m2, furnished, for rent")
        assert result["area_unit"] == "sqm"
        assert result["area_size"] == Decimal("45")
        assert result["property_type"] == "studio"
        assert result["furnishing"] == "furnished"

    def test_truncates_excerpt_to_1500_chars(self):
        long = "Apartment " * 500
        result = extract_listing_specs(long)
        assert len(result["raw_text_excerpt"]) == 1500

    def test_matches_extracted_listing_specs_schema(self):
        result = extract_listing_specs(
            "Apartment 3 bedrooms 2 bathrooms 150 sqm in Beirut, 1 parking"
        )
        # All optional fields should be accepted by the schema when omitted.
        specs = ExtractedListingSpecs(
            area_size=result.get("area_size"),
            area_unit=result.get("area_unit"),
            bedrooms=result.get("bedrooms"),
            bathrooms=result.get("bathrooms"),
            parking=result.get("parking"),
            property_type=result.get("property_type"),
            listing_purpose=result.get("listing_purpose"),
            furnishing=result.get("furnishing"),
            city=result.get("city"),
            address=result.get("address"),
            field_confidence=result.get("field_confidence", {}),
            source_snippets=result.get("source_snippets", {}),
        )
        assert specs.bedrooms == 3
        assert specs.area_unit == "sqm"
        assert specs.field_confidence["bedrooms"] == "high"

    async def test_llm_normalization_overrides_messy_ocr(self):
        mock_provider = MagicMock()
        mock_provider.chat = AsyncMock(
            return_value={
                "text": json.dumps(
                    {
                        "bedrooms": 4,
                        "bathrooms": 2,
                        "area_size": 140,
                        "area_unit": "sqm",
                        "city": "Tripoli",
                        "property_type": "apartment",
                        "field_confidence": {"bedrooms": "high"},
                        "source_snippets": {"bedrooms": "four bedrooms"},
                    }
                )
            }
        )
        with patch("app.ai.ocr.get_chat_provider", return_value=mock_provider):
            result = await extract_listing_specs_via_llm("four bedrooms, 2 bath, 140 sqm in Tripoli")

        assert result["bedrooms"] == 4
        assert result["bathrooms"] == 2
        assert result["city"] == "Tripoli"
        assert result["field_confidence"]["bedrooms"] == "high"

    async def test_llm_normalization_falls_back_on_error(self):
        with patch("app.ai.ocr.get_chat_provider", side_effect=RuntimeError("no provider")):
            result = await extract_listing_specs_via_llm("3 bedrooms 2 bathrooms 150 sqm in Beirut")

        assert result["bedrooms"] == 3
        assert result["city"] == "Beirut"


# ── OCR upload validation ───────────────────────────────────────────────────


class TestValidateOcrUpload:
    def test_pdf_under_8mb_passes(self):
        # 5 MB of zeroes, content_type pdf
        data = b"x" * (5 * 1024 * 1024)
        _validate_ocr_upload(data, "application/pdf", "specs.pdf")

    def test_jpeg_under_8mb_passes(self):
        data = b"y" * (1 * 1024 * 1024)
        _validate_ocr_upload(data, "image/jpeg", "specs.jpg")

    def test_png_under_8mb_passes(self):
        data = b"z" * (1 * 1024 * 1024)
        _validate_ocr_upload(data, "image/png", "specs.png")

    def test_webp_under_8mb_passes(self):
        data = b"w" * (1 * 1024 * 1024)
        _validate_ocr_upload(data, "image/webp", "specs.webp")

    def test_oversized_pdf_rejected(self):
        from app.common.exceptions import AppException
        data = b"x" * (11 * 1024 * 1024)
        with pytest.raises(AppException) as exc:
            _validate_ocr_upload(data, "application/pdf", "big.pdf")
        assert exc.value.error_code == "OCR_TOO_LARGE"

    def test_unsupported_type_rejected(self):
        from app.common.exceptions import AppException
        data = b"abc" * 100
        with pytest.raises(AppException) as exc:
            _validate_ocr_upload(data, "application/zip", "specs.zip")
        assert exc.value.error_code == "OCR_WRONG_TYPE"

    def test_empty_bytes_rejected(self):
        from app.common.exceptions import AppException
        with pytest.raises(AppException) as exc:
            _validate_ocr_upload(b"   \n  ", "application/pdf", "empty.pdf")
        assert exc.value.error_code == "OCR_EMPTY"


# ── JSON parsing helper ─────────────────────────────────────────────────────


class TestParseJsonObject:
    def test_valid_json_object(self):
        assert _parse_json_object('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}

    def test_json_in_code_fence(self):
        text = '```json\n{"title": "Hello", "description": "World"}\n```'
        result = _parse_json_object(text)
        assert result["title"] == "Hello"

    def test_invalid_json_raises(self):
        with pytest.raises(RuntimeError, match="JSON object"):
            _parse_json_object("not json at all")

    def test_json_array_raises(self):
        with pytest.raises(RuntimeError, match="JSON object"):
            _parse_json_object("[1, 2, 3]")


# ── Job state machine ───────────────────────────────────────────────────────


class TestJobStateMachine:
    def _make_job(self):
        from app.ai.models import AgencyAIJob
        return AgencyAIJob(
            id=uuid4(),
            job_type=JOB_TYPE_OCR_EXTRACTION,
            status=JOB_STATUS_QUEUED,
            tenant_id=uuid4(),
            actor_user_id=uuid4(),
        )

    def test_new_job_sets_queued(self):
        job = new_job(
            job_type=JOB_TYPE_OCR_EXTRACTION,
            tenant_id=uuid4(),
            actor_user_id=uuid4(),
        )
        assert job.status == JOB_STATUS_QUEUED
        assert job.expires_at is not None

    def test_mark_processing_transitions_state(self):
        job = self._make_job()
        mark_processing(job)
        assert job.status == JOB_STATUS_PROCESSING
        assert job.started_at is not None

    def test_mark_completed_sets_terminal(self):
        job = self._make_job()
        mark_processing(job)
        mark_completed(job, {"foo": "bar"})
        assert job.status == JOB_STATUS_COMPLETED
        assert job.completed_at is not None
        assert job.result_payload == {"foo": "bar"}

    def test_mark_failed_captures_reason(self):
        job = self._make_job()
        mark_processing(job)
        mark_failed(job, "ocr_timeout")
        assert job.status == JOB_STATUS_FAILED
        assert job.error_message == "ocr_timeout"
        assert job.completed_at is not None

    def test_mark_completed_sets_payload_and_status(self):
        job = self._make_job()
        mark_processing(job)
        mark_completed(job, {"status": "blocked", "reason": "policy_violation"})
        assert job.status == JOB_STATUS_COMPLETED
        assert job.result_payload == {"status": "blocked", "reason": "policy_violation"}


# ── Listing snapshot helper ─────────────────────────────────────────────────


class TestPublicListingSnapshot:
    def test_builds_snapshot_with_id_and_title(self):
        listing = MagicMock()
        listing.id = uuid4()
        listing.title = "Test Listing"
        listing.city = "Beirut"
        listing.price = 1000
        snapshot = _public_listing_snapshot(listing)
        assert snapshot["title"] == "Test Listing"
        assert snapshot["city"] == "Beirut"
        assert snapshot["price"] == "1000"  # snapshot converts to string for json

    def test_snapshot_handles_missing_optional_fields(self):
        listing = MagicMock()
        listing.id = uuid4()
        listing.title = "Minimal"
        listing.description = None
        listing.property_type = None
        listing.listing_purpose = None
        listing.price = None
        listing.currency = None
        listing.bedrooms = None
        listing.bathrooms = None
        listing.parking = None
        listing.floor = None
        listing.area_size = None
        listing.area_unit = None
        listing.furnishing = None
        listing.location_text = None
        listing.address = None
        listing.city = None
        listing.country = None
        snapshot = _public_listing_snapshot(listing)
        assert snapshot["title"] == "Minimal"
        assert snapshot["price"] is None
        assert snapshot["area_size"] is None
