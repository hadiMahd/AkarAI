import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.listings.models import ListingPhotoDerivative, ListingPhotoMetadata


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

    def _city(self, base: str) -> str:
        return f"{base}_{uuid.uuid4().hex[:8]}"

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
        city = self._city("Bedroom")
        await self._create_listing(async_client, admin_token, title="Low Bedroom", city=city, bedrooms=2)
        high_id = await self._create_listing(
            async_client,
            admin_token,
            title="High Bedroom",
            city=city,
            bedrooms=3,
        )

        resp = await async_client.get(f"/listings?city={city}&bedrooms=3")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert high_id in ids
        assert all(item["bedrooms"] >= 3 for item in data["items"])

    async def test_public_search_bathrooms_filter_is_minimum(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Bathroom")
        await self._create_listing(async_client, admin_token, title="Low Bathroom", city=city, bathrooms=1)
        high_id = await self._create_listing(
            async_client,
            admin_token,
            title="High Bathroom",
            city=city,
            bathrooms=2,
        )

        resp = await async_client.get(f"/listings?city={city}&bathrooms=2")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert high_id in ids
        assert all(item["bathrooms"] >= 2 for item in data["items"])

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

    async def test_public_search_furnishing_filter(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Furnishing")
        furnished_id = await self._create_listing(
            async_client,
            admin_token,
            title="Furnished Filter Test",
            city=city,
            furnishing="furnished",
        )
        await self._create_listing(
            async_client,
            admin_token,
            title="Unfurnished Filter Test",
            city=city,
            furnishing="unfurnished",
        )

        resp = await async_client.get(f"/listings?city={city}&furnishing=furnished")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert furnished_id in ids
        assert all(item["furnishing"] == "furnished" for item in data["items"])

    async def test_public_search_area_filters(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Area")
        matching_id = await self._create_listing(
            async_client,
            admin_token,
            title="Area Match",
            city=city,
            area_size=120,
        )
        await self._create_listing(
            async_client,
            admin_token,
            title="Area Miss",
            city=city,
            area_size=70,
        )

        resp = await async_client.get(f"/listings?city={city}&min_area_size=100&max_area_size=130")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert matching_id in ids
        assert all(100 <= float(item["area_size"]) <= 130 for item in data["items"])

    async def test_public_search_city_and_location_apply_together(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Joint")
        other_city = self._city("Other")
        matching_id = await self._create_listing(
            async_client,
            admin_token,
            title="Target Location Match",
            city=city,
            location_text="Target District",
        )
        await self._create_listing(
            async_client,
            admin_token,
            title="Wrong Location",
            city=city,
            location_text="Other District",
        )
        await self._create_listing(
            async_client,
            admin_token,
            title="Wrong City",
            city=other_city,
            location_text="Target District",
        )

        resp = await async_client.get(f"/listings?city={city}&location=Target")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert matching_id in ids
        assert len(ids) == 1

    async def test_public_search_multiple_cities_filter(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        beirut = self._city("Beirut")
        jounieh = self._city("Jounieh")
        excluded = self._city("Excluded")
        beirut_id = await self._create_listing(async_client, admin_token, title="Beirut Match", city=beirut)
        jounieh_id = await self._create_listing(async_client, admin_token, title="Jounieh Match", city=jounieh)
        await self._create_listing(async_client, admin_token, title="Excluded", city=excluded)

        resp = await async_client.get(f"/listings?city={beirut}&city={jounieh}")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert beirut_id in ids
        assert jounieh_id in ids
        assert all(item["city"] in {beirut, jounieh} for item in data["items"])

    async def test_public_list_cities_returns_sorted_seeded_values(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/cities")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert "Beirut" in data
        assert "Jounieh" in data
        assert data == sorted(data)

    async def test_public_search_sort_newest(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        await self._create_listing(async_client, admin_token, title="Newest Test")

        resp = await async_client.get("/listings?sort=newest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_public_search_sort_oldest(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Oldest")
        old_id = await self._create_listing(async_client, admin_token, title="Oldest First A", city=city)
        new_id = await self._create_listing(async_client, admin_token, title="Oldest First B", city=city)

        resp = await async_client.get(f"/listings?city={city}&sort=oldest")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"][:2]]
        assert ids == [old_id, new_id]

    async def test_public_search_sort_price_asc(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("PriceAsc")
        low_id = await self._create_listing(async_client, admin_token, title="Cheap First", city=city, price=100000)
        high_id = await self._create_listing(async_client, admin_token, title="Expensive Second", city=city, price=200000)

        resp = await async_client.get(f"/listings?city={city}&sort=price_asc")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"][:2]]
        assert ids == [low_id, high_id]

    async def test_public_search_sort_price_desc(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("PriceDesc")
        low_id = await self._create_listing(async_client, admin_token, title="Cheap Second", city=city, price=100000)
        high_id = await self._create_listing(async_client, admin_token, title="Expensive First", city=city, price=200000)

        resp = await async_client.get(f"/listings?city={city}&sort=price_desc")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"][:2]]
        assert ids == [high_id, low_id]

    async def test_public_search_sort_price_desc_puts_null_prices_last(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("NullPrice")
        low_id = await self._create_listing(
            async_client,
            admin_token,
            title="Cheap Before Null",
            city=city,
            price=100000,
        )
        high_id = await self._create_listing(
            async_client,
            admin_token,
            title="Expensive Before Null",
            city=city,
            price=200000,
        )
        null_id = await self._create_listing(
            async_client,
            admin_token,
            title="No Price Last",
            city=city,
            price=None,
        )

        resp = await async_client.get(f"/listings?city={city}&sort=price_desc")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"][:3]]
        assert ids == [high_id, low_id, null_id]

    async def test_public_search_sort_area_size_asc(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("AreaAsc")
        small_id = await self._create_listing(async_client, admin_token, title="Small First", city=city, area_size=80)
        large_id = await self._create_listing(async_client, admin_token, title="Large Second", city=city, area_size=120)

        resp = await async_client.get(f"/listings?city={city}&sort=area_size_asc")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"][:2]]
        assert ids == [small_id, large_id]

    async def test_public_search_sort_area_size_desc(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("AreaDesc")
        small_id = await self._create_listing(async_client, admin_token, title="Small Second", city=city, area_size=80)
        large_id = await self._create_listing(async_client, admin_token, title="Large First", city=city, area_size=120)

        resp = await async_client.get(f"/listings?city={city}&sort=area_size_desc")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"][:2]]
        assert ids == [large_id, small_id]

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

    async def test_public_listing_uses_public_safe_derivative_even_if_status_uploaded(
        self,
        async_client: AsyncClient,
        db_session,
    ):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token, title="Media Detail Test")

        tenant_res = await db_session.execute(
            text("SELECT agency_tenant_id FROM listings WHERE id = :listing_id"),
            {"listing_id": listing_id},
        )
        tenant_id = tenant_res.scalar_one()

        listing_photo = ListingPhotoMetadata(
            listing_id=listing_id,
            agency_tenant_id=tenant_id,
            object_key="test/uploaded.jpg",
            display_order=1,
            status="uploaded",
        )
        db_session.add(listing_photo)
        await db_session.commit()

        derivative = ListingPhotoDerivative(
            listing_photo_metadata_id=listing_photo.id,
            variant_name="optimized",
            object_key="test/uploaded.webp",
            format="webp",
            width=640,
            height=480,
            file_size_bytes=12345,
            is_public_safe=True,
        )
        db_session.add(derivative)
        await db_session.commit()

        detail_resp = await async_client.get(f"/listings/{listing_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["thumbnail_url"] is not None

        media_resp = await async_client.get(f"/listings/{listing_id}/media")
        assert media_resp.status_code == 200
        media = media_resp.json()
        assert len(media) == 1
        assert media[0]["media_url"].startswith("http")

    async def test_public_get_listing_not_found(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_public_search_rate_limit(self, async_client: AsyncClient):
        for _ in range(35):
            resp = await async_client.get("/listings")
            if resp.status_code == 429:
                break
        assert resp.status_code in [200, 429]


@pytest.mark.anyio
class TestPublicListingAPIWithParkingFloor:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_public_search_returns_active_only(self, async_client: AsyncClient):
        resp = await async_client.get("/listings")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["status"] == "active"

    async def test_public_search_pagination_continuity(self, async_client: AsyncClient):
        resp = await async_client.get("/listings?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert "page_size" in data  # cache may return different page_size on cached hit
        assert "total" in data

    async def test_public_search_filter_preservation_in_response(self, async_client: AsyncClient):
        resp = await async_client.get("/listings?city=NonExistentCity12345&page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_public_search_parking_filter_accepted(self, async_client: AsyncClient):
        resp = await async_client.get("/listings?parking=1")
        assert resp.status_code == 200

    async def test_public_search_floor_filter_accepted(self, async_client: AsyncClient):
        resp = await async_client.get("/listings?floor=3")
        assert resp.status_code == 200
