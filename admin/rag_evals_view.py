"""RAG eval results admin view."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st

from admin.api_client import AdminAPIClient, AdminAPIError
from admin.auth import AuthState
from admin.components import (
    render_backend_error,
    render_empty_state,
    render_loading,
    render_section,
)


def _client() -> AdminAPIClient:
    return AdminAPIClient(base_url=os.getenv("BACKEND_URL", "http://backend:8000"))


def _format_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _format_ms(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.0f} ms"


def _format_mode(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.replace("_", " ").title()


def _run_state(run: dict[str, Any]) -> tuple[str, str]:
    if run.get("passed"):
        return "Passing", "success"
    if run.get("threshold_failures"):
        return "Failing", "error"
    return "Unknown", "info"


def _render_latest_summary(run: dict[str, Any]) -> None:
    state_text, state_tone = _run_state(run)
    with st.container(border=True):
        top = st.columns([3, 1, 1])
        with top[0]:
            st.markdown(f"**Latest run: {run.get('run_label', 'Unnamed run')}**")
            st.caption(f"{_format_mode(run.get('mode'))} | Created {run.get('created_at', '-')}")
        with top[1]:
            st.metric("State", state_text)
        with top[2]:
            st.metric("Examples", run.get("total_examples", 0))

        if state_tone == "error":
            st.error("Threshold failures: " + ", ".join(run.get("threshold_failures", [])))
        elif state_tone == "success":
            st.success("All blocking thresholds passed.")
        else:
            st.info("Run state could not be determined.")

        metrics = st.columns(4)
        with metrics[0]:
            st.metric("Faithfulness", _format_metric(run.get("faithfulness")))
            st.metric("Context precision", _format_metric(run.get("context_precision")))
        with metrics[1]:
            st.metric("Context recall", _format_metric(run.get("context_recall")))
            st.metric("Answer relevancy", _format_metric(run.get("answer_relevancy")))
        with metrics[2]:
            st.metric("Hit@1", _format_metric(run.get("hit_at_1")))
            st.metric("Hit@5", _format_metric(run.get("hit_at_5")))
        with metrics[3]:
            st.metric("Tenant leakage", run.get("tenant_leakage_count", 0))
            st.metric("p95 latency", _format_ms(run.get("p95_latency_ms")))

        st.caption(
            f"Judge failures: {run.get('judge_failures', 0)} | "
            f"Passed examples: {run.get('passed_examples', 0)} | "
            f"Failed examples: {run.get('failed_examples', 0)}"
        )


def _render_runs_table(items: list[dict[str, Any]]) -> None:
    rows = [
        {
            "Run": item.get("run_label"),
            "Mode": _format_mode(item.get("mode")),
            "State": _run_state(item)[0],
            "Created": item.get("created_at"),
            "Faithfulness": _format_metric(item.get("faithfulness")),
            "Hit@5": _format_metric(item.get("hit_at_5")),
            "Leakage": item.get("tenant_leakage_count", 0),
            "p95 latency": _format_ms(item.get("p95_latency_ms")),
        }
        for item in items
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_example_rows(examples: list[dict[str, Any]]) -> None:
    if not examples:
        render_empty_state("No example rows were stored for this run.")
        return
    rows = [
        {
            "Example": example.get("example_id"),
            "Query": example.get("query"),
            "Tenant fixture": example.get("tenant_fixture"),
            "Expected": _format_mode(example.get("expected_behavior")),
            "Passed": "Yes" if example.get("passed") else "No",
            "Answer status": example.get("answer_status") or "-",
            "Faithfulness": _format_metric(example.get("faithfulness")),
            "Hit@5": "Yes"
            if example.get("hit_at_5")
            else "No"
            if example.get("hit_at_5") is not None
            else "-",
            "Latency": _format_ms(example.get("latency_ms")),
        }
        for example in examples
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    for example in examples:
        extra = example.get("failure_reasons") or example.get("leaked_sources")
        if not extra:
            continue
        with st.expander(f"Details: {example.get('example_id')}"):
            if example.get("failure_reasons"):
                st.markdown("**Failure reasons**")
                for item in example["failure_reasons"]:
                    st.caption(f"- {item}")
            if example.get("leaked_sources"):
                st.markdown("**Leaked sources**")
                for item in example["leaked_sources"]:
                    st.caption(f"- {item}")


def render_rag_evals(auth: AuthState) -> None:
    st.subheader("RAG Evals")
    st.caption("Latest persisted RAG evaluation results across blocking and manual runs.")

    page_size = st.selectbox("History size", [5, 10, 20, 50], index=1, key="rag_eval_page_size")
    selected_run_id = st.session_state.get("rag_eval_selected_run_id")

    with render_loading("Loading eval runs..."):
        try:
            runs_payload = _client().list_rag_eval_runs(auth.token, page=1, page_size=page_size)
        except AdminAPIError as exc:
            render_backend_error(exc)
            return

    items = runs_payload.get("items", [])
    if not items:
        render_empty_state("No RAG eval results have been recorded yet.")
        return

    latest = items[0]
    _render_latest_summary(latest)

    render_section("Recent runs")
    _render_runs_table(items)

    run_options = {
        f"{item.get('run_label')} ({_format_mode(item.get('mode'))})": item.get("run_id")
        for item in items
    }
    labels = list(run_options.keys())
    default_index = 0
    if selected_run_id:
        for index, label in enumerate(labels):
            if run_options[label] == selected_run_id:
                default_index = index
                break
    selected_label = st.selectbox(
        "Inspect run", labels, index=default_index, key="rag_eval_run_select"
    )
    current_run_id = run_options[selected_label]
    st.session_state["rag_eval_selected_run_id"] = current_run_id

    with render_loading("Loading run details..."):
        try:
            detail = _client().get_rag_eval_run(auth.token, current_run_id)
        except AdminAPIError as exc:
            render_backend_error(exc)
            return

    render_section("Per-example results")
    _render_example_rows(detail.get("examples", []))


__all__ = ["render_rag_evals"]
