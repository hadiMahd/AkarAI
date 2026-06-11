import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestSupportEmployeeRestrictions:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_support_cannot_update_agency_profile(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.put("/agencies/me/profile", json={
            "display_name": "Should Fail",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    async def test_support_cannot_create_employee(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.post("/agencies/me/employees", json={
            "work_email": f"support_{uuid.uuid4().hex[:8]}@agency.test",
            "display_name": "Should Fail",
            "role_slug": "support_employee",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    async def test_support_cannot_update_employee(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        list_resp = await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})
        employees = list_resp.json()["items"]
        if employees:
            employee_id = employees[0]["id"]
            resp = await async_client.patch(f"/agencies/me/employees/{employee_id}", json={
                "display_name": "Should Fail",
            }, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 403

    async def test_support_cannot_deactivate_employee(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        list_resp = await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})
        employees = list_resp.json()["items"]
        if employees:
            employee_id = employees[0]["id"]
            resp = await async_client.delete(f"/agencies/me/employees/{employee_id}", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 403

    async def test_support_cannot_create_listing(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.post("/agency/listings", json={
            "title": "Should Fail",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    async def test_support_cannot_create_viewing_slot(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        create_resp = await async_client.post("/agency/listings", json={
            "title": "Slot Test",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
        }, headers={"Authorization": f"Bearer {admin_token}"})
        listing_id = create_resp.json()["id"]

        support_token = await self._login(async_client, "support@akarai.test")
        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)

        resp = await async_client.post(f"/agency/listings/{listing_id}/viewing-slots", json={
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "capacity": 5,
        }, headers={"Authorization": f"Bearer {support_token}"})
        assert resp.status_code == 403

    async def test_support_can_read_agency_profile(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get("/agencies/me/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in [200, 404]

    async def test_support_can_read_employees(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    async def test_support_can_read_listings(self, async_client: AsyncClient):
        token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get("/agency/listings", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    async def test_support_can_read_viewing_slots(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        create_resp = await async_client.post("/agency/listings", json={
            "title": "Read Test",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
        }, headers={"Authorization": f"Bearer {admin_token}"})
        listing_id = create_resp.json()["id"]

        support_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get(f"/agency/listings/{listing_id}/viewing-slots", headers={"Authorization": f"Bearer {support_token}"})
        assert resp.status_code == 200
