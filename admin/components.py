"""Reusable Streamlit components for the platform admin dashboard.

These helpers handle:
- The login form
- The dashboard access gate
- Backend error rendering
- Empty / loading state placeholders
- Filter scope widgets
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Callable

import streamlit as st

from admin.api_client import AdminAPIError, AdminAPIClient
from admin.auth import (
    AuthState,
    PLATFORM_DASHBOARD_PERMISSION,
    get_auth_state,
    sign_in,
    sign_out,
)


# ---------------------------------------------------------------------------
# Access gate
# ---------------------------------------------------------------------------


def require_dashboard_access(client_factory: Callable[[], AdminAPIClient] | None = None) -> AuthState:
    """Block the page unless the actor is a platform admin with dashboard access."""
    state = get_auth_state()
    if state is None:
        st.warning("You must sign in as a platform admin to use this dashboard.")
        render_login_form(client_factory or AdminAPIClient)
        st.stop()

    if state.role != "platform_admin":
        st.error(
            "This dashboard is restricted to platform administrators. "
            "Your account is signed in but does not have platform-admin access."
        )
        render_sign_out_button()
        st.stop()

    if not state.has_dashboard_access():
        st.error(
            "Your platform-admin account is missing the "
            f"`{PLATFORM_DASHBOARD_PERMISSION}` permission required for "
            "this dashboard. Contact another platform admin to grant access."
        )
        render_sign_out_button()
        st.stop()

    return state


# ---------------------------------------------------------------------------
# Login form
# ---------------------------------------------------------------------------


def render_login_form(client: AdminAPIClient) -> None:
    st.subheader("Sign in")
    st.caption(
        "Use the same platform-admin credentials you use elsewhere in AqarAi."
    )
    with st.form("platform_admin_login", clear_on_submit=False):
        email = st.text_input("Email", key="platform_admin_email")
        password = st.text_input(
            "Password", type="password", key="platform_admin_password"
        )
        submitted = st.form_submit_button("Sign in")
        if submitted:
            _attempt_login(client, email, password)


def _attempt_login(client: AdminAPIClient, email: str, password: str) -> None:
    if not email or not password:
        st.error("Email and password are required.")
        return
    try:
        sign_in(client, email=email.strip(), password=password)
    except AdminAPIError as exc:
        if exc.status_code in (401, 403):
            st.error("Sign in failed. Check your credentials and try again.")
        else:
            render_backend_error(exc)
        return
    st.success("Signed in.")
    st.rerun()


def render_sign_out_button() -> None:
    if st.button("Sign out"):
        sign_out()
        st.rerun()


# ---------------------------------------------------------------------------
# Error rendering
# ---------------------------------------------------------------------------


def render_backend_error(exc: AdminAPIError) -> None:
    if exc.status_code == 0:
        st.error(
            "Cannot reach the platform admin backend right now. "
            "Try again in a moment."
        )
        return
    if exc.status_code == 401:
        st.error("Your session expired. Please sign in again.")
        sign_out()
        st.rerun()
    if exc.status_code == 403:
        st.error(
            "You do not have access to this dashboard view. "
            "Ask a platform admin to grant the required permission."
        )
        return
    st.error(f"Backend error: {exc.detail}")


# ---------------------------------------------------------------------------
# Filter scope widget
# ---------------------------------------------------------------------------


RANGE_PRESETS = ("last_7_days", "last_30_days", "last_90_days", "custom")


def _resolve_date_range(
    preset: str,
    custom_from: date | None,
    custom_to: date | None,
    max_window_days: int,
) -> tuple[date, date] | None:
    today = date.today()
    if preset == "last_7_days":
        return today - timedelta(days=7), today
    if preset == "last_30_days":
        return today - timedelta(days=30), today
    if preset == "last_90_days":
        return today - timedelta(days=90), today
    if preset == "custom":
        if custom_from is None or custom_to is None:
            return None
        if custom_from > custom_to:
            return None
        if (custom_to - custom_from).days > max_window_days:
            return None
        return custom_from, custom_to
    return None


def render_filter_scope(
    *,
    cities: list[str] | None = None,
    property_types: list[str] | None = None,
    listing_purposes: list[str] | None = None,
    max_window_days: int = 90,
    key_prefix: str = "filter_scope",
) -> dict[str, Any] | None:
    """Render the dashboard filter scope and return a normalized dict or None.

    Returns ``None`` when the date range is invalid (so the caller can show
    an inline empty state without firing the backend request).
    """
    cities = list(cities or [])
    property_types = list(property_types or [])
    listing_purposes = list(listing_purposes or [])

    with st.container(border=True):
        st.markdown("**Scope**")
        cols = st.columns([1, 1, 1])
        with cols[0]:
            preset = st.selectbox(
                "Date range",
                RANGE_PRESETS,
                index=1,
                key=f"{key_prefix}_preset",
                format_func=lambda v: v.replace("_", " ").title(),
            )
        with cols[1]:
            city = st.selectbox(
                "City",
                ["all"] + cities,
                key=f"{key_prefix}_city",
                index=0,
            )
        with cols[2]:
            property_type = st.selectbox(
                "Property type",
                ["all"] + property_types,
                key=f"{key_prefix}_property_type",
                index=0,
            )

        purpose = st.selectbox(
            "Listing purpose",
            ["all"] + listing_purposes,
            key=f"{key_prefix}_listing_purpose",
            index=0,
        )

        custom_from = custom_to = None
        if preset == "custom":
            custom_cols = st.columns(2)
            with custom_cols[0]:
                custom_from = st.date_input(
                    "From",
                    value=date.today() - timedelta(days=30),
                    key=f"{key_prefix}_custom_from",
                )
            with custom_cols[1]:
                custom_to = st.date_input(
                    "To",
                    value=date.today(),
                    key=f"{key_prefix}_custom_to",
                )

        range_value = _resolve_date_range(preset, custom_from, custom_to, max_window_days)
        if range_value is None:
            st.warning(
                f"Please pick a date range of at most {max_window_days} days "
                "and ensure the start date is before the end date."
            )
            return None

        return {
            "date_from": range_value[0].isoformat(),
            "date_to": range_value[1].isoformat(),
            "range_preset": preset,
            "city": None if city == "all" else city,
            "property_type": None if property_type == "all" else property_type,
            "listing_purpose": None if purpose == "all" else purpose,
        }


# ---------------------------------------------------------------------------
# Section header / empty state helpers
# ---------------------------------------------------------------------------


def render_section(title: str, caption: str | None = None) -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def render_empty_state(message: str) -> None:
    st.info(message)


def render_loading(text: str = "Loading…"):
    return st.spinner(text)


# ---------------------------------------------------------------------------
# KPI tile
# ---------------------------------------------------------------------------


def render_kpi(label: str, value: Any, help: str | None = None) -> None:
    st.metric(label, value, help=help)


__all__ = [
    "RANGE_PRESETS",
    "require_dashboard_access",
    "render_login_form",
    "render_sign_out_button",
    "render_backend_error",
    "render_filter_scope",
    "render_section",
    "render_empty_state",
    "render_loading",
    "render_kpi",
    "sign_in",
    "sign_out",
    "get_auth_state",
]
