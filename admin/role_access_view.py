"""Role and access overview admin view."""
from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

import streamlit as st

from admin.api_client import AdminAPIError, AdminAPIClient
from admin.auth import AuthState
from admin.components import (
    render_backend_error,
    render_empty_state,
    render_loading,
)


def _client() -> AdminAPIClient:
    return AdminAPIClient(base_url=os.getenv("BACKEND_URL", "http://backend:8000"))


ROLE_PURPOSES = {
    "platform_admin": "Monitors platform-wide health, access, and redacted operational activity.",
    "agency_admin": "Runs one agency tenant and manages listings, leads, viewings, and agency workflows.",
    "support_employee": "Supports a tenant with constrained read-oriented access.",
    "user": "Browses the marketplace, saves listings, compares homes, and sends inquiries.",
}


DOMAIN_LABELS = {
    "auth": "Authentication",
    "agency": "Agency operations",
    "listing": "Listings",
    "lead": "Leads",
    "viewing": "Viewings",
    "platform": "Platform oversight",
    "other": "Other",
}


def _group_permissions(permissions: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for permission in permissions:
        if ":" in permission:
            domain, remainder = permission.split(":", 1)
        else:
            domain, remainder = "other", permission
        bucket = domain if domain in {"auth", "agency", "listing", "lead", "viewing", "platform"} else "other"
        grouped[bucket].append(remainder)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _humanize_permission(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _render_role_card(role: dict[str, Any]) -> None:
    display_name = role.get("display_name", role.get("role_slug", "unknown"))
    purpose = ROLE_PURPOSES.get(role.get("role_slug"), "")
    permissions = role.get("granted_permissions", [])
    grouped = _group_permissions(permissions) if permissions else {}
    surfaces = role.get("surface_access", [])
    restricted = role.get("restricted_surfaces", [])

    with st.container(border=True):
        top_cols = st.columns([3, 1, 1, 1])
        with top_cols[0]:
            st.subheader(display_name)
            st.caption(purpose or f"Role slug: {role.get('role_slug')}")
        with top_cols[1]:
            st.metric("Permission groups", len(grouped))
        with top_cols[2]:
            st.metric("Allowed surfaces", len(surfaces))
        with top_cols[3]:
            st.metric("Blocked surfaces", len(restricted))

        content_cols = st.columns([3, 2, 2])
        with content_cols[0]:
            st.markdown("**Granted permissions**")
            if grouped:
                for domain, values in grouped.items():
                    label = DOMAIN_LABELS.get(domain, domain.title())
                    formatted = ", ".join(_humanize_permission(value) for value in values)
                    st.caption(f"**{label}:** {formatted}")
            else:
                st.caption("No permissions granted.")

        with content_cols[1]:
            st.markdown("**Allowed surfaces**")
            if surfaces:
                for surface in surfaces:
                    st.caption(f"- {surface}")
            else:
                st.caption("No allowed surfaces listed.")

        with content_cols[2]:
            st.markdown("**Blocked surfaces**")
            if restricted:
                for surface in restricted:
                    st.caption(f"- {surface}")
            else:
                st.caption("No blocked surfaces listed.")


def render_role_access_overview(auth: AuthState) -> None:
    st.subheader("Role & Access Overview")
    st.caption("Read-only summary of who can access what across the product.")

    with render_loading("Loading role overview..."):
        try:
            payload = _client().get_role_overview(auth.token)
        except AdminAPIError as exc:
            render_backend_error(exc)
            return

    items = payload.get("items", [])
    if not items:
        render_empty_state("No roles configured in the system.")
        return

    for role in items:
        _render_role_card(role)


__all__ = ["render_role_access_overview"]
