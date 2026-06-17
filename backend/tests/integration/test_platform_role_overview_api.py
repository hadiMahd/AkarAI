"""Integration tests for ``/api/v1/platform/roles/overview``."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


PLATFORM_ADMIN_EMAIL = "platform.admin@akarai.test"
AGENCY_ADMIN_EMAIL = "agency.admin@akarai.test"


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.anyio
class TestPlatformRoleOverviewAPI:
    @pytest.mark.integration
    async def test_platform_admin_can_read_role_overview(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/roles/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        slugs = {item["role_slug"] for item in data["items"]}
        for expected in ("user", "agency_admin", "support_employee", "platform_admin"):
            assert expected in slugs
        for item in data["items"]:
            for key in (
                "role_slug",
                "display_name",
                "granted_permissions",
                "surface_access",
                "restricted_surfaces",
            ):
                assert key in item

    @pytest.mark.integration
    async def test_agency_admin_is_forbidden(self, async_client: AsyncClient):
        token = await _login(async_client, AGENCY_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/roles/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.integration
    async def test_unauthenticated_is_rejected(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/platform/roles/overview")
        assert resp.status_code == 401

    @pytest.mark.integration
    async def test_platform_admin_has_dashboard_read_in_granted(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/roles/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        pa = next(item for item in items if item["role_slug"] == "platform_admin")
        assert "platform:dashboard_read" in pa["granted_permissions"]
