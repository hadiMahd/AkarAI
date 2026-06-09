import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
class TestEmployeeDeactivation:
    async def test_employee_deactivation_requires_permission(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.post(
            "/auth/employees/00000000-0000-0000-0000-000000000001/deactivate",
            json={"reason": "contract ended"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_employee_deactivation_with_permission(self, async_client: AsyncClient):
        login_resp = await async_client.post("/auth/login", json={
            "email": "agency.admin@akarai.test",
            "password": "Test1234!",
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.post(
            "/auth/employees/00000000-0000-0000-0000-000000000001/deactivate",
            json={"reason": "contract ended"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in (404,)

    async def test_deactivation_without_auth(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/employees/00000000-0000-0000-0000-000000000001/deactivate",
            json={"reason": "test"},
        )
        assert response.status_code == 401
