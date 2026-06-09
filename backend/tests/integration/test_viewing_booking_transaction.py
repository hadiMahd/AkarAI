import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest.mark.anyio
class TestViewingBookingTransaction:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Viewing Booking Test Listing",
            "description": "For viewing booking tests",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 200000,
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

    async def test_book_viewing_creates_scheduled_viewing(self, async_client: AsyncClient):
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
        assert data["listing_id"] == listing_id
        assert data["viewing_slot_id"] == slot_id

    async def test_book_viewing_increments_reserved_count(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.get(
            f"/agency/listings/{listing_id}/viewing-slots",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        slots = resp.json()
        slot = next(s for s in slots if s["id"] == slot_id)
        assert slot["reserved_count"] == 1

    async def test_book_viewing_creates_status_history(self, async_client: AsyncClient):
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
        data = resp.json()
        assert data["status"] == "scheduled"

    async def test_book_viewing_capacity_check(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        starts = datetime.now(timezone.utc) + timedelta(days=2)
        ends = starts + timedelta(hours=1)
        slot_resp = await async_client.post(
            f"/agency/listings/{listing_id}/viewing-slots",
            json={
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
                "capacity": 1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        slot_id = slot_resp.json()["id"]

        user1_token = await self._login(async_client, "user@akarai.test")
        resp1 = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        assert resp1.status_code == 201

        user2_token = await self._login(async_client, "support@akarai.test")
        resp2 = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp2.status_code == 409

    async def test_book_viewing_requires_auth(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
        )
        assert resp.status_code == 401

    async def test_book_viewing_invalid_slot(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404
