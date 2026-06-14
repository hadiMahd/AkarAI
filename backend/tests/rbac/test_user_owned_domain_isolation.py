import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest.mark.anyio
class TestUserOwnedDomainIsolation:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Isolation Test Listing",
            "description": "For isolation tests",
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

    async def test_saved_listing_user_isolation(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user1_token = await self._login(async_client, "user@akarai.test")
        await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get(
            "/me/saved-listings",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["user_id"] != user1_token

    async def test_comparison_session_user_isolation(self, async_client: AsyncClient):
        user1_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "User1 Comparison"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        session_id = session_resp.json()["id"]

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get(
            f"/me/comparison-sessions/{session_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 404

    async def test_comparison_session_items_user_isolation(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user1_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "User1 Comparison"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        session_id = session_resp.json()["id"]

        await async_client.post(
            f"/me/comparison-sessions/{session_id}/items",
            json={"listing_id": listing_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.post(
            f"/me/comparison-sessions/{session_id}/items",
            json={"listing_id": listing_id},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 404

    async def test_viewing_detail_user_isolation(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user1_token = await self._login(async_client, "user@akarai.test")
        booking_resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        viewing_id = booking_resp.json()["id"]

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.get(
            f"/me/viewings/{viewing_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 403

    async def test_unsave_listing_user_isolation(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user1_token = await self._login(async_client, "user@akarai.test")
        await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.delete(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 204

        resp = await async_client.get(
            "/me/saved-listings",
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_update_comparison_session_user_isolation(self, async_client: AsyncClient):
        user1_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "User1 Comparison"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        session_id = session_resp.json()["id"]

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.patch(
            f"/me/comparison-sessions/{session_id}",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 404

    async def test_delete_comparison_session_user_isolation(self, async_client: AsyncClient):
        user1_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "User1 Comparison"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        session_id = session_resp.json()["id"]

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.delete(
            f"/me/comparison-sessions/{session_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 404

    async def test_remove_comparison_item_user_isolation(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user1_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "User1 Comparison"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        session_id = session_resp.json()["id"]

        await async_client.post(
            f"/me/comparison-sessions/{session_id}/items",
            json={"listing_id": listing_id},
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        user2_token = await self._login(async_client, "support@akarai.test")
        resp = await async_client.delete(
            f"/me/comparison-sessions/{session_id}/items/{listing_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert resp.status_code == 404
