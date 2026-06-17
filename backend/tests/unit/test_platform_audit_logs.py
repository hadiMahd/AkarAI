"""Unit tests for the platform audit-log redaction and feature mapping.

The audit log view is read-only and must:
- Map each ``action`` to a stable ``feature_area`` label
- Drop keys from ``event_metadata`` that are not on the safe allow-list
- Sanitize remaining string values through the existing PII/secret pipeline
"""
from __future__ import annotations

import pytest

from app.audit.feature_mapping import (
    ALLOWED_METADATA_KEYS,
    FEATURE_AREAS,
    _redact_audit_metadata,
    build_audit_view_metadata,
    normalize_feature_area,
)


class TestFeatureAreaMapping:
    @pytest.mark.parametrize(
        "action, expected",
        [
            ("auth.sign_in.success", "auth"),
            ("auth.refresh.failure", "auth"),
            ("agency.employee_deactivated", "agency"),
            ("listing.created", "listing"),
            ("listing.image_uploaded", "media"),
            ("lead.reviewed", "lead"),
            ("viewing.scheduled", "viewing"),
            ("search.log_search", "search"),
            ("rag.document_uploaded", "rag"),
            ("agency_ai.spec_extraction.queued", "ai_assistant"),
            ("platform_dashboard.insights.read", "platform_dashboard"),
            ("some.unknown.action", "other"),
            ("", "other"),
        ],
    )
    def test_action_prefix_to_feature_area(self, action, expected):
        assert normalize_feature_area(action) == expected

    def test_resource_type_fallback(self):
        assert normalize_feature_area(None, "search_log") == "search"
        assert normalize_feature_area("foo", "rag_document") == "rag"
        assert normalize_feature_area("foo", "unknown_thing") == "other"

    def test_feature_areas_are_closed(self):
        for area in (
            "auth",
            "agency",
            "listing",
            "lead",
            "viewing",
            "search",
            "rag",
            "ai_assistant",
            "media",
            "platform_dashboard",
            "other",
        ):
            assert area in FEATURE_AREAS


class TestRedactAuditMetadata:
    def test_drops_unknown_keys(self):
        safe = _redact_audit_metadata(
            {"actor_role": "platform_admin", "password": "supersecret"}
        )
        assert "actor_role" in safe
        assert "password" not in safe

    def test_truncates_ip(self):
        safe = _redact_audit_metadata(
            {"ip_address_truncated": "192.168.1.42", "actor_role": "user"}
        )
        assert safe["ip_address_truncated"] == "192.168.1.0"

    def test_empty_metadata(self):
        assert _redact_audit_metadata(None) == {}
        assert _redact_audit_metadata({}) == {}

    def test_allow_list_contains_expected_keys(self):
        for key in (
            "actor_role",
            "feature_area",
            "ip_address_truncated",
            "required_permission",
            "tenant_scope",
        ):
            assert key in ALLOWED_METADATA_KEYS


class TestBuildAuditViewMetadata:
    def test_combines_actor_role_and_safe_meta(self):
        out = build_audit_view_metadata(
            {"actor_role": "platform_admin", "password": "leak"},
            actor_role="platform_admin",
        )
        assert out["actor_role"] == "platform_admin"
        assert "password" not in out

    def test_handles_missing_metadata(self):
        out = build_audit_view_metadata(None, actor_role="user")
        assert out == {"actor_role": "user"}
