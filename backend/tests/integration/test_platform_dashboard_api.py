"""Integration tests for ``/api/v1/platform/dashboard/insights``.

The tests are structured against the live DB+Redis fixtures and the
existing seeded test users. They will run when the Docker Compose
stack is brought up. Until then they remain a documented contract.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


PLATFORM_ADMIN_EMAIL = "platform.admin@akarai.test"
PLATFORM_ADMIN_PASSWORD = "Test1234!"
AGENCY_ADMIN_EMAIL = "agency.admin@akarai.test"
AGENCY_ADMIN_PASSWORD = "Test1234!"


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    token = await _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
class TestPlatformDashboardInsightsAPI:
    @pytest.mark.integration
    async def test_platform_admin_with_permission_can_read_insights(
        self, async_client: AsyncClient
    ):
        headers = await _auth_headers(
            async_client, PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD
        )
        resp = await async_client.get(
            "/api/v1/platform/dashboard/insights",
            params={"range_preset": "last_30_days"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "scope" in data
        assert "search_volume_total" in data
        assert "search_volume_trend" in data
        assert "top_areas" in data
        assert "top_budget_bands" in data
        assert "top_property_types" in data
        assert "demand_gaps" in data

    @pytest.mark.integration
    async def test_unauthenticated_request_is_rejected(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/platform/dashboard/insights")
        assert resp.status_code == 401

    @pytest.mark.integration
    async def test_agency_admin_is_rejected(self, async_client: AsyncClient):
        headers = await _auth_headers(
            async_client, AGENCY_ADMIN_EMAIL, AGENCY_ADMIN_PASSWORD
        )
        resp = await async_client.get(
            "/api/v1/platform/dashboard/insights",
            params={"range_preset": "last_7_days"},
            headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.integration
    async def test_filter_scope_is_echoed_back(self, async_client: AsyncClient):
        headers = await _auth_headers(
            async_client, PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD
        )
        resp = await async_client.get(
            "/api/v1/platform/dashboard/insights",
            params={
                "range_preset": "last_7_days",
                "city": "Beirut",
                "property_type": "apartment",
                "listing_purpose": "rent",
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["scope"]["city"] == "Beirut"
        assert data["scope"]["property_type"] == "apartment"
        assert data["scope"]["listing_purpose"] == "rent"
        assert data["scope"]["range_preset"] == "last_7_days"

    @pytest.mark.integration
    async def test_search_logs_appear_in_segments(self, async_client: AsyncClient, db_session, test_tenant):
        from app.search.models import SearchLog

        now = datetime.now(timezone.utc)
        log = SearchLog(
            id=uuid.uuid4(),
            source_mode="manual",
            event_type="manual_search",
            filters={"city": "Beirut", "property_type": "apartment", "max_price": 120_000},
            result_count=3,
            created_at=now,
        )
        db_session.add(log)
        await db_session.commit()
        try:
            headers = await _auth_headers(
                async_client, PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD
            )
            resp = await async_client.get(
                "/api/v1/platform/dashboard/insights",
                params={"range_preset": "last_30_days"},
                headers=headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["search_volume_total"] >= 1
            assert any(area["label"] == "beirut" for area in data["top_areas"])
        finally:
            await db_session.delete(log)
            await db_session.commit()
