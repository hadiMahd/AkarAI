"""AI audit logs admin view."""
from __future__ import annotations

import os
from typing import Any

import streamlit as st

from admin.api_client import AdminAPIError, AdminAPIClient
from admin.auth import AuthState
from admin.components import (
    render_backend_error,
    render_empty_state,
    render_loading,
    render_section,
)


FEATURE_AREAS = [
    "all",
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
]

ACTOR_ROLES = ["all", "platform_admin", "agency_admin", "support_employee", "user", "platform", "agency"]
RESULTS = ["all", "success", "failure", "unknown"]


def _client() -> AdminAPIClient:
    return AdminAPIClient(base_url=os.getenv("BACKEND_URL", "http://backend:8000"))


def _labelize(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.replace("_", " ").replace(".", " ").strip().title()


def _humanize_action(action: str | None) -> str:
    if not action:
        return "Unknown event"
    friendly = {
        "platform_dashboard.insights.read": "Viewed marketplace insights",
        "platform_dashboard.audit_logs.read": "Viewed audit activity",
        "platform_dashboard.roles.read": "Viewed role overview",
        "auth.login": "User sign-in attempt",
        "auth.login.success": "User signed in",
        "auth.logout": "User signed out",
        "agency_ai.spec_extraction.created": "Spec extraction started",
        "agency_ai.spec_extraction.completed": "Spec extraction completed",
        "lead.processing.spam.completed": "Spam classification completed",
        "lead.processing.level.completed": "Lead priority classified",
    }
    return friendly.get(action, _labelize(action))


def _format_scope_label(value: str | None) -> str:
    mapping = {
        "platform": "Platform-wide",
        "agency": "Agency-scoped",
    }
    return mapping.get(value or "", _labelize(value))


def _format_result(value: str | None) -> tuple[str, str]:
    mapping = {
        "success": ("OK", "success"),
        "failure": ("Needs attention", "error"),
        "cache_hit": ("Cached", "info"),
        "fresh": ("Fresh", "success"),
        "unknown": ("Unknown", "caption"),
    }
    return mapping.get(value or "", (_labelize(value), "caption"))


def _pretty_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {_labelize(key): value for key, value in metadata.items()}


def _render_log_row(log: dict[str, Any]) -> None:
    cols = st.columns([4, 2, 2, 2, 2, 1])
    event_id = log.get("id", "-")
    action = log.get("action", "")
    metadata = log.get("redacted_metadata", {}) or {}
    scope_label = log.get("tenant_scope_label", "unknown")
    with cols[0]:
        st.markdown(f"**{_humanize_action(action)}**")
        st.caption(_labelize(action))
    with cols[1]:
        st.caption(_labelize(log.get("feature_area", "other")))
    with cols[2]:
        st.caption(_labelize(log.get("actor_role", "unknown")))
    with cols[3]:
        st.caption(_format_scope_label(scope_label))
    with cols[4]:
        st.caption(log.get("created_at", "-"))
    with cols[5]:
        result_text, tone = _format_result(log.get("result", ""))
        if tone == "success":
            st.success(result_text)
        elif tone == "error":
            st.error(result_text)
        elif tone == "info":
            st.info(result_text)
        else:
            st.caption(result_text or "-")

    with st.expander("View details", expanded=False):
        st.markdown(f"**Event ID:** `{event_id}`")
        st.markdown(f"**Raw action:** `{action or '-'}`")
        st.markdown(f"**Actor role:** {_labelize(log.get('actor_role', 'unknown'))}")
        st.markdown(f"**Scope:** {_format_scope_label(scope_label)}")
        actor_user_id = log.get("actor_user_id")
        if actor_user_id:
            st.markdown(f"**Actor user ID:** `{actor_user_id}`")
        if metadata:
            st.json(_pretty_metadata(metadata))


def _render_paginator(page: int, total: int, has_next: bool, has_previous: bool) -> None:
    cols = st.columns([1, 1, 3])
    prev_clicked = False
    next_clicked = False
    with cols[0]:
        if has_previous:
            prev_clicked = st.button("Previous page", key=f"prev_{page}")
    with cols[1]:
        if has_next:
            next_clicked = st.button("Next page", key=f"next_{page}")
    with cols[2]:
        st.caption(f"Page {page} - {total} log entries total")

    if prev_clicked:
        st.session_state["audit_page"] = max(1, page - 1)
        st.rerun()
    if next_clicked:
        st.session_state["audit_page"] = page + 1
        st.rerun()


def render_ai_audit_logs(auth: AuthState) -> None:
    st.subheader("AI Audit Logs")
    st.caption("Redacted operational activity across platform workflows. Read-only.")

    with st.container(border=True):
        st.markdown("**Filters**")
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            feature_area = st.selectbox(
                "Focus area",
                FEATURE_AREAS,
                key="audit_feature",
                index=10,
                format_func=lambda value: "All activity" if value == "all" else _labelize(value),
            )
        with fc2:
            actor_role = st.selectbox(
                "Actor role",
                ACTOR_ROLES,
                key="audit_actor",
                format_func=lambda value: "All roles" if value == "all" else _labelize(value),
            )
        with fc3:
            result_filter = st.selectbox(
                "Result",
                RESULTS,
                key="audit_result",
                format_func=lambda value: "All results" if value == "all" else _labelize(value),
            )
        with fc4:
            page_size = st.selectbox(
                "Page size",
                [10, 20, 50, 100],
                index=1,
                key="audit_page_size",
            )

    page = st.session_state.get("audit_page", 1)

    with render_loading("Loading audit logs..."):
        try:
            payload = _client().list_audit_logs(
                auth.token,
                page=page,
                page_size=page_size,
                feature_area=None if feature_area == "all" else feature_area,
                actor_role=None if actor_role == "all" else actor_role,
                result=None if result_filter == "all" else result_filter,
            )
        except AdminAPIError as exc:
            render_backend_error(exc)
            return

    items = payload.get("items", [])
    total = payload.get("total", 0)
    has_next = payload.get("has_next", False)
    has_previous = payload.get("has_previous", False)

    render_section(f"Audit entries ({total})")
    if not items:
        render_empty_state("No audit log entries match the current filters.")
        return

    cols = st.columns([4, 2, 2, 2, 2, 1])
    with cols[0]:
        st.markdown("**Event**")
    with cols[1]:
        st.markdown("**Area**")
    with cols[2]:
        st.markdown("**Actor**")
    with cols[3]:
        st.markdown("**Scope**")
    with cols[4]:
        st.markdown("**Time**")
    with cols[5]:
        st.markdown("**Result**")

    for log in items:
        _render_log_row(log)

    st.divider()
    _render_paginator(page, total, has_next, has_previous)


__all__ = [
    "ACTOR_ROLES",
    "FEATURE_AREAS",
    "RESULTS",
    "render_ai_audit_logs",
]
