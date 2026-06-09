import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
class TestTenantIsolation:
    async def test_tenant_context_endpoint_returns_context(self, async_client: AsyncClient):
        login_resp = await async_client.post("/auth/login", json={
            "email": "agency.admin@akarai.test",
            "password": "Test1234!",
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.get("/tenant/context", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert "actor_id" in data
        assert "role" in data
        assert "permissions" in data
        assert "tenant_id" in data
        assert "membership_id" in data
        assert "is_platform_actor" in data

    async def test_tenant_context_without_auth(self, async_client: AsyncClient):
        response = await async_client.get("/tenant/context")
        assert response.status_code == 401

    async def test_platform_admin_no_tenant(self, async_client: AsyncClient):
        login_resp = await async_client.post("/auth/login", json={
            "email": "platform.admin@akarai.test",
            "password": "Test1234!",
        })
        assert login_resp.status_code == 200
        access_token = login_resp.json()["access_token"]

        response = await async_client.get("/tenant/context", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] is None
        assert data["is_platform_actor"] is True
