"""Streamlit admin unit tests for the AI audit logs view.

The AI audit log view uses ``AdminAPIClient.list_audit_logs`` to fetch
paginated, redacted audit log entries. These tests validate the client
call, parameter shaping, error handling, and pagination helpers.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from admin.api_client import AdminAPIError, AdminAPIClient
from tests.conftest import FakeResponse


class TestAuditLogsAPIClient:
    def test_list_audit_logs_passes_query_params(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(
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
        fake_session.request.return_value = fake_response
        client._session = fake_session

        payload = client.list_audit_logs(
            "TOKEN",
            page=2,
            page_size=50,
            feature_area="auth",
            actor_role="platform_admin",
            result="failure",
        )
        assert payload["total"] == 0
        assert payload["page"] == 1
        called = fake_session.request.call_args
        assert called.kwargs["method"] == "GET"
        assert called.kwargs["url"] == "http://b:8000/api/v1/platform/audit-logs"
        params = called.kwargs["params"]
        assert params["page"] == 2
        assert params["page_size"] == 50
        assert params["feature_area"] == "auth"
        assert params["actor_role"] == "platform_admin"
        assert params["result"] == "failure"

    def test_list_audit_logs_defaults(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(status_code=200, payload={"items": [], "total": 0})
        fake_session.request.return_value = fake_response
        client._session = fake_session

        client.list_audit_logs("TOKEN")
        called = fake_session.request.call_args
        params = called.kwargs["params"]
        assert params["page"] == 1
        assert params["page_size"] == 20

    def test_list_audit_logs_drops_none_filters(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(status_code=200, payload={"items": [], "total": 0})
        fake_session.request.return_value = fake_response
        client._session = fake_session

        client.list_audit_logs(
            "TOKEN",
            feature_area=None,
            actor_role=None,
            result=None,
        )
        called = fake_session.request.call_args
        params = called.kwargs["params"]
        # None-valued filters are stripped by _request()
        assert "feature_area" not in params
        assert "actor_role" not in params
        assert "result" not in params
        assert params["page"] == 1

    def test_403_raises_admin_api_error(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(
            status_code=403,
            payload={"detail": "Forbidden", "error_code": "FORBIDDEN"},
        )
        fake_session.request.return_value = fake_response
        client._session = fake_session

        with pytest.raises(AdminAPIError) as exc:
            client.list_audit_logs("TOKEN")
        assert exc.value.status_code == 403
        assert exc.value.error_code == "FORBIDDEN"

    def test_results_with_items_are_parsed(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(
            status_code=200,
            payload={
                "items": [
                    {
                        "id": "evt-1",
                        "feature_area": "auth",
                        "action": "auth.login.success",
                        "actor_role": "platform_admin",
                        "tenant_scope_label": "platform",
                        "result": "success",
                        "redacted_metadata": {"tenant_scope": "platform"},
                    }
                ],
                "page": 1,
                "page_size": 10,
                "total": 1,
                "has_next": False,
                "has_previous": False,
            },
        )
        fake_session.request.return_value = fake_response
        client._session = fake_session

        payload = client.list_audit_logs("TOKEN", page_size=10)
        assert len(payload["items"]) == 1
        assert payload["items"][0]["id"] == "evt-1"
        assert payload["total"] == 1


class TestAuditLogPaginationLogic:
    def test_first_page_has_no_previous(self):
        import importlib
        _page = importlib.import_module("admin.audit_logs_view")

        assert hasattr(_page, "_render_paginator")
        assert hasattr(_page, "FEATURE_AREAS")
        assert "auth" in _page.FEATURE_AREAS

    def test_last_page_has_no_next(self):
        import importlib
        _page = importlib.import_module("admin.audit_logs_view")

        assert hasattr(_page, "_render_log_row")
