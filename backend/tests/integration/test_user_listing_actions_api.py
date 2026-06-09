import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestUserListingActionsAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "User Action Test Listing",
            "description": "For user action tests",
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

    async def test_save_listing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["listing_id"] == listing_id

    async def test_save_listing_duplicate_prevention(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        resp1 = await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp1.status_code == 200

        resp2 = await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["id"] == resp1.json()["id"]

    async def test_list_saved_listings(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.get(
            "/me/saved-listings",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "items" in data

    async def test_unsave_listing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.delete(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    async def test_create_comparison_session(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Comparison"

    async def test_list_comparison_sessions(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.get(
            "/me/comparison-sessions",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_get_comparison_session(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        create_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        session_id = create_resp.json()["id"]

        resp = await async_client.get(
            f"/me/comparison-sessions/{session_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == session_id

    async def test_update_comparison_session(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        create_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        session_id = create_resp.json()["id"]

        resp = await async_client.patch(
            f"/me/comparison-sessions/{session_id}",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_delete_comparison_session(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        create_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        session_id = create_resp.json()["id"]

        resp = await async_client.delete(
            f"/me/comparison-sessions/{session_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    async def test_add_comparison_item(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        session_id = session_resp.json()["id"]

        resp = await async_client.post(
            f"/me/comparison-sessions/{session_id}/items",
            json={"listing_id": listing_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["listing_id"] == listing_id

    async def test_add_comparison_item_four_item_limit(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_ids = []
        for i in range(5):
            lid = await self._create_listing(async_client, admin_token)
            listing_ids.append(lid)

        user_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        session_id = session_resp.json()["id"]

        for i in range(4):
            resp = await async_client.post(
                f"/me/comparison-sessions/{session_id}/items",
                json={"listing_id": listing_ids[i]},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert resp.status_code == 201

        resp = await async_client.post(
            f"/me/comparison-sessions/{session_id}/items",
            json={"listing_id": listing_ids[4]},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409

    async def test_remove_comparison_item(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        session_resp = await async_client.post(
            "/me/comparison-sessions",
            json={"name": "Test Comparison"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        session_id = session_resp.json()["id"]

        await async_client.post(
            f"/me/comparison-sessions/{session_id}/items",
            json={"listing_id": listing_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.delete(
            f"/me/comparison-sessions/{session_id}/items/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    async def test_saved_listings_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/me/saved-listings")
        assert resp.status_code == 401

    async def test_comparison_sessions_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/me/comparison-sessions")
        assert resp.status_code == 401
