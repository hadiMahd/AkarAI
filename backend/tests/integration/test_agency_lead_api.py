import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestAgencyLeadAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Test Listing",
            "description": "A test property",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 250000,
            "currency": "USD",
            "bedrooms": 2,
            "bathrooms": 1,
            "area_size": 85.5,
            "area_unit": "sqm",
            "furnishing": "furnished",
            "location_text": "Test City",
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "status": "active",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_list_agency_leads_empty(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agency/leads", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert "has_previous" in data

    async def test_list_agency_leads_with_data(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"name": "Test Lead", "email": "lead@test.com", "message": "Interested"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201

        resp = await async_client.get("/agency/leads", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_get_agency_lead(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        inquiry_resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"name": "Get Test", "email": "get@test.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        lead_id = inquiry_resp.json()["id"]

        resp = await async_client.get(f"/agency/leads/{lead_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == lead_id
        assert data["name"] == "Get Test"

    async def test_update_lead_status(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        inquiry_resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"name": "Status Test", "email": "status@test.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        lead_id = inquiry_resp.json()["id"]

        resp = await async_client.patch(
            f"/agency/leads/{lead_id}",
            json={"status": "reviewed"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "reviewed"

    async def test_review_lead(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        inquiry_resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"name": "Review Test", "email": "review@test.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        lead_id = inquiry_resp.json()["id"]

        resp = await async_client.post(
            f"/agency/leads/{lead_id}/review",
            json={"outcome": "interested", "notes": "Good prospect"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["outcome"] == "interested"
        assert data["notes"] == "Good prospect"

    async def test_get_lead_not_found(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        fake_id = str(uuid.uuid4())
        resp = await async_client.get(f"/agency/leads/{fake_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404

    async def test_update_lead_invalid_transition(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        inquiry_resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"name": "Transition Test", "email": "trans@test.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        lead_id = inquiry_resp.json()["id"]

        resp = await async_client.patch(
            f"/agency/leads/{lead_id}",
            json={"status": "reviewed"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        resp = await async_client.patch(
            f"/agency/leads/{lead_id}",
            json={"status": "new"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_list_agency_leads_pagination(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/leads?page=1&page_size=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_agency_lead_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/agency/leads")
        assert resp.status_code == 401

    async def test_agency_lead_requires_tenant(self, async_client: AsyncClient):
        token = await self._login(async_client, "platform.admin@akarai.test")
        resp = await async_client.get("/agency/leads", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
