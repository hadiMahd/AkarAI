import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestSavedListingsWithDetails:
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

    async def test_list_saved_listings_with_details(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.get(
            "/me/saved-listings/with-details",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "items" in data
        # Check that at least one item has the listing_id we just saved
        listing_ids = [item["listing_id"] for item in data["items"]]
        assert listing_id in listing_ids

    async def test_saved_listings_persist_after_refresh(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        
        # Save a listing
        save_resp = await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert save_resp.status_code == 200

        # Verify it exists with details
        list_resp = await async_client.get(
            "/me/saved-listings/with-details",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total"] >= 1
        items = data["items"]
        # Check that our specific listing is in the results
        listing_ids = [item["listing_id"] for item in items]
        assert listing_id in listing_ids

    async def test_unsave_listing_removes_from_details(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")

        # Save a listing
        await async_client.put(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Unsave it
        unsave_resp = await async_client.delete(
            f"/me/saved-listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert unsave_resp.status_code == 204

        # Verify it is gone from the details list
        list_resp = await async_client.get(
            "/me/saved-listings/with-details",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        # Check that our specific listing is NOT in the results
        listing_ids = [item["listing_id"] for item in data["items"]]
        assert listing_id not in listing_ids

    async def test_saved_listings_with_details_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/me/saved-listings/with-details")
        assert resp.status_code == 401
