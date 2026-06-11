import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestAgencyProfileAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_get_profile(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in [200, 404]

    async def test_update_profile(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.put("/agencies/me/profile", json={
            "display_name": "Updated Agency Name",
            "description": "Updated description",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Updated Agency Name"

    async def test_update_profile_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.put("/agencies/me/profile", json={
            "display_name": "Should Fail",
        })
        assert resp.status_code == 401


@pytest.mark.anyio
class TestAgencyEmployeeAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_list_employees(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_list_employees_pagination(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/employees?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_create_employee(self, async_client: AsyncClient):
        employee_email = f"support_{uuid.uuid4().hex[:8]}@agency.test"
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.post("/agencies/me/employees", json={
            "work_email": employee_email,
            "display_name": "Created Employee",
            "role_slug": "support_employee",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "active"
        assert data["work_email"] == employee_email
        assert data["display_name"] == "Created Employee"

    async def test_get_employee(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        list_resp = await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})
        employees = list_resp.json()["items"]
        if employees:
            employee_id = employees[0]["id"]
            resp = await async_client.get(f"/agencies/me/employees/{employee_id}", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            assert resp.json()["id"] == employee_id

    async def test_get_employee_not_found(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        fake_id = str(uuid.uuid4())
        resp = await async_client.get(f"/agencies/me/employees/{fake_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    async def test_update_employee(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        list_resp = await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})
        employees = list_resp.json()["items"]
        if employees:
            employee_id = employees[0]["id"]
            resp = await async_client.patch(f"/agencies/me/employees/{employee_id}", json={
                "display_name": "Updated Employee Name",
            }, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            assert resp.json()["display_name"] == "Updated Employee Name"

    async def test_deactivate_employee(self, async_client: AsyncClient):
        employee_email = f"support_{uuid.uuid4().hex[:8]}@agency.test"
        token = await self._login(async_client, "agency.admin@akarai.test")
        create_resp = await async_client.post("/agencies/me/employees", json={
            "work_email": employee_email,
            "display_name": "Deactivate Me",
            "role_slug": "support_employee",
        }, headers={"Authorization": f"Bearer {token}"})
        employee_id = create_resp.json()["id"]

        resp = await async_client.delete(f"/agencies/me/employees/{employee_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    async def test_employee_endpoints_require_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/agencies/me/employees")
        assert resp.status_code == 401

        resp = await async_client.post("/agencies/me/employees", json={
            "work_email": f"unauthorized_{uuid.uuid4().hex[:8]}@agency.test",
            "display_name": "Unauthorized",
            "role_slug": "support_employee",
        })
        assert resp.status_code == 401
