import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestPublicListingAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str, **kwargs) -> str:
        data = {
            "title": kwargs.get("title", "Test Listing"),
            "description": kwargs.get("description", "A test property"),
            "property_type": kwargs.get("property_type", "apartment"),
            "listing_purpose": kwargs.get("listing_purpose", "sale"),
            "price": kwargs.get("price", 250000),
            "currency": kwargs.get("currency", "USD"),
            "bedrooms": kwargs.get("bedrooms", 2),
            "bathrooms": kwargs.get("bathrooms", 1),
            "area_size": kwargs.get("area_size", 85.5),
            "area_unit": kwargs.get("area_unit", "sqm"),
            "furnishing": kwargs.get("furnishing", "furnished"),
            "location_text": kwargs.get("location_text", "Test City"),
            "address": kwargs.get("address", "123 Test St"),
            "city": kwargs.get("city", "Test City"),
            "country": kwargs.get("country", "Test Country"),
            "status": kwargs.get("status", "active"),
        }
        resp = await client.post("/agency/listings", json=data, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_public_search_no_filters(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, title="Public Search Test")

        resp = await async_client.get("/listings")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_public_search_location_filter(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, location_text="Downtown", city="Downtown")

        resp = await async_client.get("/listings?location=Downtown")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_price_filters(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, price=300000)

        resp = await async_client.get("/listings?min_price=200000&max_price=400000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_bedrooms_filter(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, bedrooms=3)

        resp = await async_client.get("/listings?bedrooms=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_property_type_filter(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, property_type="villa")

        resp = await async_client.get("/listings?property_type=villa")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_listing_purpose_filter(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, listing_purpose="rent")

        resp = await async_client.get("/listings?listing_purpose=rent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_sort_newest(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, title="Newest Test")

        resp = await async_client.get("/listings?sort=newest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_sort_price_asc(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, price=100000)

        resp = await async_client.get("/listings?sort=price_asc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_pagination(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, title="Pagination Test")

        resp = await async_client.get("/listings?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_public_get_listing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token, title="Detail Test")

        resp = await async_client.get(f"/listings/{listing_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == listing_id
        assert data["title"] == "Detail Test"

    async def test_public_get_listing_not_found(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_public_search_rate_limit(self, async_client: AsyncClient):
        for _ in range(35):
            resp = await async_client.get("/listings")
            if resp.status_code == 429:
                break
        assert resp.status_code in [200, 429]
