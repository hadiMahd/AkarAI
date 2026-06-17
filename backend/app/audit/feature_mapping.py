"""Audit-log helpers for the platform admin dashboard.

This module is intentionally tiny and only knows how to:
- map an audit ``action`` prefix (and a ``resource_type`` hint) onto a
  dashboard-friendly ``feature_area`` label
- decide which top-level metadata fields are safe to expose after
  redaction
- normalize the existing ``rag.redaction`` PII redaction for the
  dashboard audit views
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from app.rag.redaction import sanitize_payload


# Dashboard feature areas — keep this enum closed and documented.
FEATURE_AREAS = frozenset(
    {
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
    }
)


# Action-prefix → feature_area mapping. Lookups are case-insensitive.
_ACTION_PREFIX_MAP: tuple[tuple[str, str], ...] = (
    ("listing.image", "media"),
    ("listing.photo", "media"),
    ("auth.", "auth"),
    ("agency_ai.", "ai_assistant"),
    ("ai_assistant.", "ai_assistant"),
    ("platform_dashboard.", "platform_dashboard"),
    ("agency.", "agency"),
    ("listing.", "listing"),
    ("lead.", "lead"),
    ("viewing.", "viewing"),
    ("search.", "search"),
    ("rag.", "rag"),
    ("media.", "media"),
    ("photo", "media"),
)


_RESOURCE_TYPE_MAP: dict[str, str] = {
    "user": "auth",
    "session": "auth",
    "agency": "agency",
    "agency_tenant": "agency",
    "agency_employee_membership": "agency",
    "listing": "listing",
    "saved_listing": "listing",
    "comparison_session": "listing",
    "lead": "lead",
    "viewing_slot": "viewing",
    "scheduled_viewing": "viewing",
    "search_log": "search",
    "rag_document": "rag",
    "rag_chunk": "rag",
    "agency_ai_job": "ai_assistant",
    "agency_assistant_tool_invocation": "ai_assistant",
    "listing_photo_metadata": "media",
    "audit_log": "platform_dashboard",
}


_DEFAULT_FEATURE_AREA = "other"


def normalize_feature_area(action: str | None, resource_type: str | None = None) -> str:
    """Map an audit log row to a dashboard ``feature_area`` label."""
    if action:
        normalized = action.strip().lower()
        for prefix, area in _ACTION_PREFIX_MAP:
            if normalized.startswith(prefix):
                return area
    if resource_type and resource_type in _RESOURCE_TYPE_MAP:
        return _RESOURCE_TYPE_MAP[resource_type]
    return _DEFAULT_FEATURE_AREA


# Top-level metadata keys that are safe to show directly on the dashboard
# after secret-pattern + PII redaction. Anything else is dropped.
ALLOWED_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "actor_role",
        "feature_area",
        "ip_address_truncated",
        "required_permission",
        "tenant_scope",
        "scope",
        "action_label",
        "result_label",
    }
)


def _redact_audit_metadata(
    metadata: dict[str, Any] | None,
    *,
    allowed_keys: Iterable[str] = ALLOWED_METADATA_KEYS,
) -> dict[str, Any]:
    """Apply redaction to an audit row's ``event_metadata`` payload.

    - Drops keys that are not on the safe allow-list.
    - Sanitizes remaining string values through the existing
      ``rag.redaction.sanitize_payload`` pipeline.
    - Truncates IP addresses to a stable /24 prefix only.
    """
    if not metadata or not isinstance(metadata, dict):
        return {}
    allowed = set(allowed_keys)
    safe: dict[str, Any] = {}
    ip_value: str | None = None
    for key, value in metadata.items():
        if key not in allowed:
            continue
        if key == "ip_address_truncated" and isinstance(value, str):
            parts = value.split(".")
            if len(parts) == 4:
                ip_value = ".".join(parts[:3]) + ".0"
            continue
        safe[key] = value
    safe = sanitize_payload(safe)
    if ip_value is not None:
        safe["ip_address_truncated"] = ip_value
    return safe


def build_audit_view_metadata(
    metadata: dict[str, Any] | None,
    *,
    actor_role: str | None = None,
) -> dict[str, Any]:
    """Combine row-level fields with a safe, redacted copy of metadata."""
    out: dict[str, Any] = {}
    if actor_role:
        out["actor_role"] = actor_role
    safe_meta = _redact_audit_metadata(metadata)
    out.update(safe_meta)
    return out


__all__ = [
    "ALLOWED_METADATA_KEYS",
    "FEATURE_AREAS",
    "build_audit_view_metadata",
    "normalize_feature_area",
]
