"""Marketplace insights admin view."""
from __future__ import annotations

import os
from typing import Any

import streamlit as st

from admin.api_client import AdminAPIError, AdminAPIClient
from admin.auth import AuthState
from admin.components import (
    render_backend_error,
    render_empty_state,
    render_filter_scope,
    render_loading,
    render_section,
)


KNOWN_PROPERTY_TYPES = ["apartment", "villa", "townhouse", "studio", "office", "shop", "land"]
KNOWN_LISTING_PURPOSES = ["sale", "rent"]


def _client() -> AdminAPIClient:
    return AdminAPIClient(base_url=os.getenv("BACKEND_URL", "http://backend:8000"))


def _titleize(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.replace("_", " ").strip().title()


def _format_share(value: float | None) -> str:
    share = value or 0.0
    percent = share * 100
    if percent <= 0:
        return "0%"
    if percent < 1:
        return "<1%"
    if percent < 10:
        return f"{percent:.1f}%"
    return f"{percent:.0f}%"


def _format_gap_label(direction: str | None) -> str:
    mapping = {
        "undersupplied": "High demand, thin supply",
        "balanced": "Balanced demand and supply",
        "oversupplied": "Supply ahead of demand",
    }
    return mapping.get(direction or "", _titleize(direction))


def _render_kpis(payload: dict[str, Any]) -> None:
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total searches", payload.get("search_volume_total", 0))
    with cols[1]:
        st.metric("Cities with demand", len(payload.get("top_areas", [])))
    with cols[2]:
        st.metric("Property types in demand", len(payload.get("top_property_types", [])))
    with cols[3]:
        st.metric("Demand gaps surfaced", len(payload.get("demand_gaps", [])))


def _render_operator_summary(payload: dict[str, Any]) -> None:
    top_area = next(iter(payload.get("top_areas", [])), None)
    top_type = next(iter(payload.get("top_property_types", [])), None)
    top_budget = next(iter(payload.get("top_budget_bands", [])), None)
    top_gap = next(iter(payload.get("demand_gaps", [])), None)

    summary_parts = []
    if top_area:
        summary_parts.append(
            f"Strongest city demand is in **{_titleize(top_area.get('label'))}** "
            f"({_format_share(top_area.get('share'))} of scoped searches)."
        )
    if top_type:
        summary_parts.append(
            f"Most requested property type is **{_titleize(top_type.get('label'))}**."
        )
    if top_budget:
        summary_parts.append(
            f"Most active budget band is **{top_budget.get('label')}**."
        )
    if top_gap:
        summary_parts.append(
            f"Biggest supply mismatch is **{_titleize(top_gap.get('dimension_label'))}** "
            f"with **{_format_gap_label(top_gap.get('gap_direction'))}**."
        )

    if not summary_parts:
        render_empty_state("No clear marketplace signal is available for the selected scope yet.")
        return

    with st.container(border=True):
        st.markdown("**Operator summary**")
        for part in summary_parts:
            st.markdown(f"- {part}")


def _render_trend(trend: list[dict[str, Any]]) -> None:
    if not trend:
        render_empty_state("No search activity in this scope yet.")
        return
    rows = [
        {
            "Period start": point.get("bucket_start"),
            "Period end": point.get("bucket_end"),
            "Searches": point.get("search_count", 0),
        }
        for point in trend
    ]
    st.line_chart(
        data=[row["Searches"] for row in rows],
        use_container_width=True,
    )
    with st.expander("View period breakdown", expanded=False):
        st.dataframe(rows, use_container_width=True)


def _render_segments(title: str, segments: list[dict[str, Any]], *, empty: str) -> None:
    render_section(title)
    if not segments:
        render_empty_state(empty)
        return
    rows = [
        {
            "Rank": s.get("rank"),
            "Segment": _titleize(s.get("label")),
            "Searches": s.get("search_count", 0),
            "Share": _format_share(s.get("share")),
        }
        for s in segments
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_demand_gaps(gaps: list[dict[str, Any]]) -> None:
    render_section("Demand gaps (city × search demand vs active supply)")
    if not gaps:
        render_empty_state("Not enough data to compute demand gaps for this scope.")
        return
    rows = [
        {
            "City": _titleize(g.get("dimension_label")),
            "Demand": g.get("demand_count", 0),
            "Supply": g.get("supply_count", 0),
            "Gap score": g.get("gap_score", 0.0),
            "Signal": _format_gap_label(g.get("gap_direction")),
        }
        for g in gaps
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_marketplace_insights(auth: AuthState) -> None:
    st.subheader("Marketplace Insights")
    st.caption(
        "Aggregate demand and supply signals across the marketplace. "
        "No agency-level drill-down is shown here."
    )

    scope = render_filter_scope(
        property_types=KNOWN_PROPERTY_TYPES,
        listing_purposes=KNOWN_LISTING_PURPOSES,
        max_window_days=90,
        key_prefix="insights",
    )
    if scope is None:
        return

    with render_loading("Loading insights..."):
        try:
            payload = _client().get_insights(
                auth.token,
                date_from=scope["date_from"],
                date_to=scope["date_to"],
                range_preset=scope["range_preset"],
                city=scope["city"],
                property_type=scope["property_type"],
                listing_purpose=scope["listing_purpose"],
            )
        except AdminAPIError as exc:
            render_backend_error(exc)
            return

    _render_kpis(payload)
    st.caption(
        f"Updated {payload.get('generated_at', 'n/a')} | "
        f"Scope {payload['scope']['date_from']} to {payload['scope']['date_to']} | "
        f"Window {_titleize(payload['scope']['range_preset'])}"
    )
    _render_operator_summary(payload)

    render_section("Search demand trend")
    _render_trend(payload.get("search_volume_trend", []))

    col1, col2 = st.columns(2)
    with col1:
        _render_segments(
            "Top cities",
            payload.get("top_areas", []),
            empty="No city-level demand data in this scope.",
        )
    with col2:
        _render_segments(
            "Top property types",
            payload.get("top_property_types", []),
            empty="No property-type data in this scope.",
        )

    _render_segments(
        "Top budget bands",
        payload.get("top_budget_bands", []),
        empty="No budget-band data in this scope.",
    )

    _render_demand_gaps(payload.get("demand_gaps", []))


__all__ = [
    "KNOWN_LISTING_PURPOSES",
    "KNOWN_PROPERTY_TYPES",
    "render_marketplace_insights",
]
