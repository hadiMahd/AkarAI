"""Streamlit entry point for the AkarAI platform admin dashboard."""
from __future__ import annotations

import os

import streamlit as st

from admin.api_client import AdminAPIClient
from admin.audit_logs_view import render_ai_audit_logs
from admin.auth import (
    AuthState,
    get_auth_state,
)
from admin.components import (
    render_backend_error,
    render_login_form,
    render_sign_out_button,
    require_dashboard_access,
)
from admin.insights_view import render_marketplace_insights
from admin.role_access_view import render_role_access_overview


st.set_page_config(
    page_title="AkarAI Platform Admin",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)


BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def _client() -> AdminAPIClient:
    return AdminAPIClient(base_url=BACKEND_URL)


def _render_home(auth: AuthState) -> None:
    st.subheader("Home")
    st.caption(
        "Read-only platform oversight for marketplace health, access posture, and audit review."
    )

    cols = st.columns(3)
    with cols[0]:
        with st.container(border=True):
            st.markdown("**Marketplace Insights**")
            st.caption("Search demand, budget bands, property mix, and supply gaps.")
    with cols[1]:
        with st.container(border=True):
            st.markdown("**AI Audit Logs**")
            st.caption("Redacted operational history with filtering by area, role, and result.")
    with cols[2]:
        with st.container(border=True):
            st.markdown("**Role & Access Overview**")
            st.caption("Readable access boundaries for every supported platform role.")

    st.divider()

    lower_cols = st.columns(2)
    with lower_cols[0]:
        st.subheader("Backend status")
        try:
            resp = _client().get_current_actor(auth.token)
            st.success(
                f"Connected — {resp.get('actor', {}).get('email', 'session ok')}"
            )
        except Exception as exc:  # noqa: BLE001
            render_backend_error(exc)
    with lower_cols[1]:
        st.subheader("Quick links")
        st.markdown(
            """
            - [User app](http://localhost:3000)
            - [Agency app](http://localhost:3001)
            - [MinIO console](http://localhost:9001)
            - [API docs](http://localhost:8000/docs)
            """
        )


def main() -> None:
    state = get_auth_state()
    if state is None:
        st.title("AkarAI Platform Admin")
        st.caption("Sign in to access the marketplace oversight dashboard.")
        render_login_form(_client())
        return

    try:
        auth = require_dashboard_access(_client)
    except st.runtime.scriptrunner.StopException:
        return

    st.title("AkarAI Platform Admin")
    st.caption("Read-only marketplace oversight for platform administrators.")

    with st.sidebar:
        st.markdown("### Operator")
        st.write(auth.name or auth.email)
        st.caption(auth.email)
        st.caption(f"{auth.role.replace('_', ' ').title()} | {len(auth.permissions)} permissions")
        if auth.permissions:
            with st.expander("View permissions", expanded=False):
                for permission in auth.permissions:
                    st.code(permission, language=None)
        render_sign_out_button()

    home_tab, insights_tab, audit_tab, role_tab = st.tabs(
        ["Home", "Marketplace Insights", "AI Audit Logs", "Role & Access Overview"]
    )
    with home_tab:
        _render_home(auth)
    with insights_tab:
        render_marketplace_insights(auth)
    with audit_tab:
        render_ai_audit_logs(auth)
    with role_tab:
        render_role_access_overview(auth)


if __name__ == "__main__":
    main()
