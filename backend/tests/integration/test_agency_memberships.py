import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
class TestAgencyMemberships:
    async def test_agency_admin_has_tenant_context(self, async_client: AsyncClient):
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
        assert data["role"] == "agency_admin"
        assert data["tenant_id"] is not None
        assert data["membership_id"] is not None

    async def test_support_employee_has_tenant_context(self, async_client: AsyncClient):
        login_resp = await async_client.post("/auth/login", json={
            "email": "support@akarai.test",
            "password": "Test1234!",
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.get("/tenant/context", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "support_employee"

    async def test_regular_user_has_no_tenant(self, async_client: AsyncClient):
        login_resp = await async_client.post("/auth/login", json={
            "email": "user@akarai.test",
            "password": "Test1234!",
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.get("/tenant/context", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] is None
