import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestAgencyViewingAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Viewing Test Listing",
            "description": "For viewing tests",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 200000,
            "currency": "USD",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_size": 50.0,
            "area_unit": "sqm",
            "furnishing": "unfurnished",
            "location_text": "Viewing City",
            "address": "456 Viewing St",
            "city": "Viewing City",
            "country": "Test Country",
            "status": "active",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _create_viewing_slot(self, client: AsyncClient, token: str, listing_id: str) -> str:
        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)
        resp = await client.post(
            f"/agency/listings/{listing_id}/viewing-slots",
            json={
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
                "capacity": 3,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_list_viewing_slots(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        await self._create_viewing_slot(async_client, admin_token, listing_id)

        resp = await async_client.get(
            f"/agency/listings/{listing_id}/viewing-slots",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_create_viewing_slot(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        starts = datetime.now(timezone.utc) + timedelta(days=2)
        ends = starts + timedelta(hours=2)
        resp = await async_client.post(
            f"/agency/listings/{listing_id}/viewing-slots",
            json={
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
                "capacity": 5,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["capacity"] == 5
        assert data["reserved_count"] == 0
        assert data["status"] == "active"

    async def test_update_viewing_slot(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        resp = await async_client.patch(
            f"/agency/listings/{listing_id}/viewing-slots/{slot_id}",
            json={"capacity": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["capacity"] == 10

    async def test_deactivate_viewing_slot(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        resp = await async_client.delete(
            f"/agency/listings/{listing_id}/viewing-slots/{slot_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

    async def test_book_viewing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id, "notes": "Want to see it"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "scheduled"
        assert data["notes"] == "Want to see it"

    async def test_list_my_viewings(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.get("/me/viewings", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "items" in data

    async def test_get_my_viewing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        booking_resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        viewing_id = booking_resp.json()["id"]

        resp = await async_client.get(
            f"/me/viewings/{viewing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == viewing_id

    async def test_list_agency_viewings(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/viewings",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    async def test_get_agency_viewing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        booking_resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        viewing_id = booking_resp.json()["id"]

        resp = await async_client.get(
            f"/agency/viewings/{viewing_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == viewing_id

    async def test_update_agency_viewing_status(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        booking_resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        viewing_id = booking_resp.json()["id"]

        resp = await async_client.patch(
            f"/agency/viewings/{viewing_id}",
            json={"status": "completed", "reason": "Visit done"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    async def test_viewing_slot_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/agency/listings/fake-id/viewing-slots")
        assert resp.status_code == 401

    async def test_book_viewing_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.post("/listings/fake-id/viewings", json={"viewing_slot_id": str(uuid.uuid4())})
        assert resp.status_code == 401

    async def test_list_my_viewings_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/me/viewings")
        assert resp.status_code == 401
