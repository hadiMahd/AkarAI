import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestAgencyEmployeeAccountCreationAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_create_employee_creates_dedicated_account(self, async_client: AsyncClient):
        employee_email = f"support_{uuid.uuid4().hex[:8]}@agency.test"
        token = await self._login(async_client, "agency.admin@akarai.test")

        create_resp = await async_client.post(
            "/agencies/me/employees",
            json={
                "work_email": employee_email,
                "display_name": "New Support Employee",
                "role_slug": "support_employee",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        assert data["work_email"] == employee_email
        assert data["display_name"] == "New Support Employee"
        assert data["status"] == "active"

        login_resp = await async_client.post(
            "/auth/login",
            json={"email": employee_email, "password": "12345678"},
        )
        assert login_resp.status_code == 200
        assert login_resp.json()["actor"]["role"] == "support_employee"

    async def test_create_employee_rejects_existing_user_email(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")

        resp = await async_client.post(
            "/agencies/me/employees",
            json={
                "work_email": "agency.admin@akarai.test",
                "display_name": "Should Fail",
                "role_slug": "support_employee",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409
        body = resp.json()
        assert "already exists" in body["detail"]
        assert body["error_code"] == "EMPLOYEE_EMAIL_EXISTS"
