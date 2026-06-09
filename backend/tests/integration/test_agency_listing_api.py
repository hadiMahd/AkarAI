import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestAgencyListingAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_list_tenant_listings(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agency/listings", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_create_listing(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.post("/agency/listings", json={
            "title": "API Test Listing",
            "description": "Created via API test",
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
        data = resp.json()
        assert data["title"] == "API Test Listing"
        assert data["status"] == "active"

    async def test_get_listing(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        create_resp = await async_client.post("/agency/listings", json={
            "title": "Get Test",
            "property_type": "villa",
            "listing_purpose": "rent",
            "price": 5000,
        }, headers={"Authorization": f"Bearer {token}"})
        listing_id = create_resp.json()["id"]

        resp = await async_client.get(f"/agency/listings/{listing_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == listing_id

    async def test_update_listing(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        create_resp = await async_client.post("/agency/listings", json={
            "title": "Update Test",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
        }, headers={"Authorization": f"Bearer {token}"})
        listing_id = create_resp.json()["id"]

        resp = await async_client.patch(f"/agency/listings/{listing_id}", json={
            "title": "Updated Title",
            "price": 150000,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        assert float(resp.json()["price"]) == 150000

    async def test_archive_listing(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        create_resp = await async_client.post("/agency/listings", json={
            "title": "Archive Test",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
            "status": "active",
        }, headers={"Authorization": f"Bearer {token}"})
        listing_id = create_resp.json()["id"]

        resp = await async_client.delete(f"/agency/listings/{listing_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    async def test_listing_endpoints_require_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/agency/listings")
        assert resp.status_code == 401

        resp = await async_client.post("/agency/listings", json={
            "title": "Should Fail",
        })
        assert resp.status_code == 401


@pytest.mark.anyio
class TestAgencyPhotoMetadataAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Photo Test Listing",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_list_photos(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        resp = await async_client.get(f"/agency/listings/{listing_id}/photos", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_photo(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        resp = await async_client.post(f"/agency/listings/{listing_id}/photos", json={
            "object_key": "test/photo1.jpg",
            "caption": "Test photo",
            "alt_text": "Alt text",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["object_key"] == "test/photo1.jpg"
        assert data["status"] == "active"

    async def test_update_photo(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        create_resp = await async_client.post(f"/agency/listings/{listing_id}/photos", json={
            "object_key": "test/photo2.jpg",
        }, headers={"Authorization": f"Bearer {token}"})
        photo_id = create_resp.json()["id"]

        resp = await async_client.patch(f"/agency/listings/{listing_id}/photos/{photo_id}", json={
            "caption": "Updated caption",
            "alt_text": "Updated alt",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["caption"] == "Updated caption"

    async def test_remove_photo(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        create_resp = await async_client.post(f"/agency/listings/{listing_id}/photos", json={
            "object_key": "test/photo3.jpg",
        }, headers={"Authorization": f"Bearer {token}"})
        photo_id = create_resp.json()["id"]

        resp = await async_client.delete(f"/agency/listings/{listing_id}/photos/{photo_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204


@pytest.mark.anyio
class TestAgencyViewingSlotAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Slot Test Listing",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_list_viewing_slots(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        resp = await async_client.get(f"/agency/listings/{listing_id}/viewing-slots", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_viewing_slot(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)

        resp = await async_client.post(f"/agency/listings/{listing_id}/viewing-slots", json={
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "capacity": 5,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["capacity"] == 5
        assert data["reserved_count"] == 0

    async def test_update_viewing_slot(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        starts = datetime.now(timezone.utc) + timedelta(days=2)
        ends = starts + timedelta(hours=1)

        create_resp = await async_client.post(f"/agency/listings/{listing_id}/viewing-slots", json={
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "capacity": 3,
        }, headers={"Authorization": f"Bearer {token}"})
        slot_id = create_resp.json()["id"]

        resp = await async_client.patch(f"/agency/listings/{listing_id}/viewing-slots/{slot_id}", json={
            "capacity": 10,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["capacity"] == 10

    async def test_deactivate_viewing_slot(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, token)

        starts = datetime.now(timezone.utc) + timedelta(days=3)
        ends = starts + timedelta(hours=1)

        create_resp = await async_client.post(f"/agency/listings/{listing_id}/viewing-slots", json={
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "capacity": 2,
        }, headers={"Authorization": f"Bearer {token}"})
        slot_id = create_resp.json()["id"]

        resp = await async_client.delete(f"/agency/listings/{listing_id}/viewing-slots/{slot_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204
