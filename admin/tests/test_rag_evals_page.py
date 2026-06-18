from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from admin.api_client import AdminAPIClient, AdminAPIError
from admin.auth import AuthState
from admin.rag_evals_view import _render_runs_table
from tests.conftest import FakeResponse


def _auth() -> AuthState:
    return AuthState(
        token="token",
        actor={
            "email": "platform.admin@akarai.test",
            "name": "Platform Admin",
            "role": "platform_admin",
            "permissions": ["platform:dashboard_read"],
        },
    )


class TestRagEvalAPIClient:
    def test_list_runs_uses_expected_path(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_session.request.return_value = FakeResponse(
            status_code=200,
            payload={
                "items": [],
                "page": 1,
                "page_size": 20,
                "total": 0,
                "has_next": False,
                "has_previous": False,
            },
        )
        client._session = fake_session

        client.list_rag_eval_runs("TOKEN", page=2, page_size=10)
        called = fake_session.request.call_args
        assert called.kwargs["url"] == "http://b:8000/api/v1/platform/rag-evals/runs"
        assert called.kwargs["params"]["page"] == 2
        assert called.kwargs["params"]["page_size"] == 10

    def test_get_run_uses_expected_path(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_session.request.return_value = FakeResponse(
            status_code=200, payload={"run": {}, "examples": []}
        )
        client._session = fake_session

        client.get_rag_eval_run("TOKEN", "run-1")
        called = fake_session.request.call_args
        assert called.kwargs["url"] == "http://b:8000/api/v1/platform/rag-evals/runs/run-1"


class TestRagEvalView:
    def test_empty_state_view_imports(self):
        import importlib

        module = importlib.import_module("admin.rag_evals_view")
        assert hasattr(module, "render_rag_evals")

    def test_backend_error_is_raised_as_admin_api_error(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_session.request.return_value = FakeResponse(
            status_code=404,
            payload={"detail": "RAG eval run not found", "error_code": "RAG_EVAL_RUN_NOT_FOUND"},
        )
        client._session = fake_session

        with pytest.raises(AdminAPIError) as exc:
            client.get_rag_eval_run("TOKEN", "missing")
        assert exc.value.error_code == "RAG_EVAL_RUN_NOT_FOUND"

    def test_runs_table_includes_classification(self, monkeypatch):
        captured = {}

        def fake_dataframe(rows, **_kwargs):
            captured["rows"] = rows

        monkeypatch.setattr("admin.rag_evals_view.st.dataframe", fake_dataframe)

        _render_runs_table([
            {
                "run_label": "ragas-test-run-1234",
                "mode": "blocking",
                "run_classification": "test",
                "passed": True,
                "created_at": "2026-06-18T00:00:00Z",
                "faithfulness": 0.9,
                "hit_at_5": 1.0,
                "tenant_leakage_count": 0,
                "p95_latency_ms": 1234,
                "threshold_failures": [],
            }
        ])

        assert captured["rows"][0]["Class"] == "test"
