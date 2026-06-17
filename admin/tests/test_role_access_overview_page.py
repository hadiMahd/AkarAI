"""Streamlit admin unit tests for the role & access overview view.

The role overview view uses ``AdminAPIClient.get_role_overview`` to fetch
the read-only role catalog. These tests validate the client call, error
handling, and role display helpers.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from admin.api_client import AdminAPIError, AdminAPIClient
from tests.conftest import FakeResponse


class TestRoleOverviewAPIClient:
    def test_get_role_overview_returns_items(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(
            status_code=200,
            payload={
                "items": [
                    {
                        "role_slug": "platform_admin",
                        "display_name": "Platform Admin",
                        "granted_permissions": ["platform:read", "platform:dashboard_read"],
                        "surface_access": ["Platform admin dashboard"],
                        "restricted_surfaces": ["Agency-scoped mutations"],
                    },
                    {
                        "role_slug": "user",
                        "display_name": "User",
                        "granted_permissions": ["user:read"],
                        "surface_access": ["Public marketplace search"],
                        "restricted_surfaces": ["Agency dashboard", "Platform admin dashboard"],
                    },
                ]
            },
        )
        fake_session.request.return_value = fake_response
        client._session = fake_session

        payload = client.get_role_overview("TOKEN")
        assert len(payload["items"]) == 2
        assert payload["items"][0]["role_slug"] == "platform_admin"
        assert payload["items"][1]["role_slug"] == "user"
        assert "Platform Admin" in [i["display_name"] for i in payload["items"]]

    def test_get_role_overview_uses_correct_path(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(status_code=200, payload={"items": []})
        fake_session.request.return_value = fake_response
        client._session = fake_session

        client.get_role_overview("TOKEN")
        called = fake_session.request.call_args
        assert called.kwargs["url"] == "http://b:8000/api/v1/platform/roles/overview"
        assert called.kwargs["method"] == "GET"

    def test_empty_items_handled(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(status_code=200, payload={"items": []})
        fake_session.request.return_value = fake_response
        client._session = fake_session

        payload = client.get_role_overview("TOKEN")
        assert payload["items"] == []

    def test_403_raises_admin_api_error(self):
        client = AdminAPIClient(base_url="http://b:8000")
        fake_session = MagicMock()
        fake_response = FakeResponse(
            status_code=403,
            payload={"detail": "Permission denied", "error_code": "FORBIDDEN"},
        )
        fake_session.request.return_value = fake_response
        client._session = fake_session

        with pytest.raises(AdminAPIError) as exc:
            client.get_role_overview("TOKEN")
        assert exc.value.status_code == 403
        assert exc.value.error_code == "FORBIDDEN"


class TestRoleOverviewPageHelpers:
    def test_role_card_function_importable(self):
        import importlib
        _page = importlib.import_module("admin.role_access_view")

        assert hasattr(_page, "_render_role_card")

    def test_client_returns_expected_base_url(self):
        client = AdminAPIClient(base_url="http://backend.test:8000")
        assert client.base_url == "http://backend.test:8000"

    def test_permissions_grouped_by_domain(self):
        from admin.role_access_view import _group_permissions

        grouped = _group_permissions(
            [
                "platform:read",
                "platform:dashboard_read",
                "listing:update",
                "custom_permission",
            ]
        )

        assert grouped["platform"] == ["dashboard_read", "read"]
        assert grouped["listing"] == ["update"]
        assert grouped["other"] == ["custom_permission"]
