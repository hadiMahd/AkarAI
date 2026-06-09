import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestViewingDetailAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Viewing Detail Test",
            "description": "For viewing detail tests",
            "property_type": "villa",
            "listing_purpose": "sale",
            "price": 500000,
            "currency": "USD",
            "bedrooms": 3,
            "bathrooms": 2,
            "area_size": 200.0,
            "area_unit": "sqm",
            "furnishing": "furnished",
            "location_text": "Detail City",
            "address": "10 Detail St",
            "city": "Detail City",
            "country": "Test Country",
            "status": "active",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _create_slot_and_book(self, client: AsyncClient, admin_token: str, user_token: str):
        listing_id = await self._create_listing(client, admin_token)
        starts = datetime.now(timezone.utc) + timedelta(days=5)
        ends = starts + timedelta(hours=2)
        slot_resp = await client.post(
            f"/agency/listings/{listing_id}/viewing-slots",
            json={
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
                "capacity": 3,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        slot_id = slot_resp.json()["id"]

        booking_resp = await client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id, "notes": "Detail test"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        viewing_id = booking_resp.json()["id"]
        return listing_id, slot_id, viewing_id

    async def test_get_my_viewing_returns_full_detail(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        user_token = await self._login(async_client, "user@akarai.test")
        _, _, viewing_id = await self._create_slot_and_book(async_client, admin_token, user_token)

        resp = await async_client.get(
            f"/me/viewings/{viewing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == viewing_id
        assert data["status"] == "scheduled"
        assert data["notes"] == "Detail test"
        assert "scheduled_start_at" in data
        assert "scheduled_end_at" in data
        assert "listing_id" in data
        assert "viewing_slot_id" in data
        assert "created_at" in data

    async def test_get_agency_viewing_returns_full_detail(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        user_token = await self._login(async_client, "user@akarai.test")
        _, _, viewing_id = await self._create_slot_and_book(async_client, admin_token, user_token)

        resp = await async_client.get(
            f"/agency/viewings/{viewing_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == viewing_id
        assert data["status"] == "scheduled"

    async def test_viewing_status_transitions_via_api(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        user_token = await self._login(async_client, "user@akarai.test")
        _, _, viewing_id = await self._create_slot_and_book(async_client, admin_token, user_token)

        resp = await async_client.patch(
            f"/agency/viewings/{viewing_id}",
            json={"status": "completed", "reason": "Successful visit"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    async def test_viewing_cannot_transition_from_terminal(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        user_token = await self._login(async_client, "user@akarai.test")
        _, _, viewing_id = await self._create_slot_and_book(async_client, admin_token, user_token)

        await async_client.patch(
            f"/agency/viewings/{viewing_id}",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await async_client.patch(
            f"/agency/viewings/{viewing_id}",
            json={"status": "scheduled"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_get_viewing_not_found(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        fake_id = str(uuid.uuid4())
        resp = await async_client.get(
            f"/me/viewings/{fake_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_get_viewing_wrong_user(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        user_token = await self._login(async_client, "user@akarai.test")
        _, _, viewing_id = await self._create_slot_and_book(async_client, admin_token, user_token)

        other_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get(
            f"/me/viewings/{viewing_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403

    async def test_list_my_viewings_pagination(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.get(
            "/me/viewings?page=1&page_size=5",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert "has_next" in data
        assert "has_previous" in data

    async def test_list_agency_viewings_pagination(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/viewings?page=1&page_size=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_viewing_slot_detail_in_response(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        starts = datetime.now(timezone.utc) + timedelta(days=7)
        ends = starts + timedelta(hours=1)
        slot_resp = await async_client.post(
            f"/agency/listings/{listing_id}/viewing-slots",
            json={
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
                "capacity": 2,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        slot_id = slot_resp.json()["id"]

        resp = await async_client.get(
            f"/agency/listings/{listing_id}/viewing-slots",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        slots = resp.json()
        assert len(slots) >= 1
        slot = next(s for s in slots if s["id"] == slot_id)
        assert slot["capacity"] == 2
        assert slot["reserved_count"] == 0
        assert slot["status"] == "active"
