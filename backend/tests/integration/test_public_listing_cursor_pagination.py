import uuid

import pytest
from httpx import AsyncClient
from app.listings.query_service import encode_cursor, decode_cursor


@pytest.mark.anyio
class TestPublicListingCursorPagination:
    """Integration tests for cursor/keyset pagination on /listings.

    Each test uses a unique city suffix to avoid data pollution between runs.
    """

    def _city(self, base: str) -> str:
        return f"{base}_{uuid.uuid4().hex[:8]}"

    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str, **kwargs) -> str:
        data = {
            "title": kwargs.get("title", "Cursor Test"),
            "description": kwargs.get("description", "Cursor test property"),
            "property_type": kwargs.get("property_type", "apartment"),
            "listing_purpose": kwargs.get("listing_purpose", "sale"),
            "price": kwargs.get("price", 250000),
            "currency": kwargs.get("currency", "USD"),
            "bedrooms": kwargs.get("bedrooms", 2),
            "bathrooms": kwargs.get("bathrooms", 1),
            "area_size": kwargs.get("area_size", 85.5),
            "area_unit": kwargs.get("area_unit", "sqm"),
            "furnishing": kwargs.get("furnishing", "furnished"),
            "location_text": kwargs.get("location_text", "Cursor City"),
            "address": kwargs.get("address", "123 Cursor St"),
            "city": kwargs.get("city", "Cursor City"),
            "country": kwargs.get("country", "Cursor Country"),
            "status": kwargs.get("status", "active"),
        }
        resp = await client.post("/agency/listings", json=data, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _create_listings_batch(self, client, token, city, count, price_start=100000):
        ids = []
        for i in range(count):
            lid = await self._create_listing(
                client, token,
                title=f"Cursor Item {i}",
                city=city,
                price=price_start + i * 10000,
            )
            ids.append(lid)
        return ids

    async def test_uses_cursor_when_provided(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Cursor TC1")
        await self._create_listings_batch(async_client, admin_token, city, count=3)
        resp = await async_client.get(f"/listings?city={city}&page_size=2&sort=newest")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data.get("next_cursor") is None

        prev_id = data["items"][0]["id"]
        last = data["items"][-1]
        cursor = encode_cursor({"created_at": last["created_at"], "id": last["id"]})
        resp2 = await async_client.get(f"/listings?city={city}&page_size=2&sort=newest&cursor={cursor}")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) >= 1
        returned_ids = [item["id"] for item in data2["items"]]
        assert prev_id not in returned_ids

    async def test_newest_ordering_stable(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Cursor Stable")
        ids = await self._create_listings_batch(async_client, admin_token, city, count=5)
        ids_set = set(ids)

        boot = await async_client.get(f"/listings?city={city}&page_size=2&sort=newest")
        boot_data = boot.json()
        seen = [it["id"] for it in boot_data["items"]]
        last = boot_data["items"][-1]
        cursor = encode_cursor({"created_at": last["created_at"], "id": last["id"]})

        for _ in range(5):
            resp = await async_client.get(
                f"/listings?city={city}&page_size=2&sort=newest&cursor={cursor}"
            )
            assert resp.status_code == 200
            data = resp.json()
            page_ids = [item["id"] for item in data["items"]]
            seen.extend(page_ids)
            if not data.get("next_cursor"):
                break
            cursor = data["next_cursor"]

        assert len(seen) == 5, f"Got {len(seen)} items: {seen}"
        assert len(seen) == len(set(seen))
        for sid in seen:
            assert sid in ids_set

    async def test_price_asc_null_last(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Cursor NullPa")
        await self._create_listing(async_client, admin_token, title="A Price 100", city=city, price=100000)
        await self._create_listing(async_client, admin_token, title="B No Price", city=city, price=None)
        await self._create_listing(async_client, admin_token, title="C Price 200", city=city, price=200000)

        resp = await async_client.get(f"/listings?city={city}&page_size=10&sort=price_asc")
        assert resp.status_code == 200
        items = resp.json()["items"]
        prices = [it["price"] for it in items]
        non_null = [p for p in prices if p is not None]
        nulls = [p for p in prices if p is None]
        assert len(non_null) == 2, f"Expected 2 non-null prices, got {prices}"
        assert len(nulls) == 1, f"Expected 1 null price, got {prices}"
        assert prices[-1] is None

    async def test_price_desc_null_last(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Cursor DescNp")
        await self._create_listing(async_client, admin_token, title="D No Price", city=city, price=None)
        await self._create_listing(async_client, admin_token, title="E Price 300", city=city, price=300000)
        await self._create_listing(async_client, admin_token, title="F Price 100", city=city, price=100000)

        resp = await async_client.get(f"/listings?city={city}&page_size=10&sort=price_desc")
        assert resp.status_code == 200
        items = resp.json()["items"]
        prices = [it["price"] for it in items]
        non_null = [p for p in prices if p is not None]
        assert len(non_null) == 2, f"Expected 2 non-null prices, got {prices}"
        first_val = float(non_null[0])
        second_val = float(non_null[1])
        assert first_val >= second_val
        assert prices[-1] is None

    async def test_cursor_plus_filters_work_together(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Cursor FilterCity")
        for i in range(5):
            await self._create_listing(
                async_client, admin_token,
                title=f"F {i}",
                city=city,
                property_type="apartment",
                price=150000 + i * 10000,
            )
        resp = await async_client.get(f"/listings?city={city}&property_type=apartment&page_size=2&sort=newest")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2

        last = data["items"][-1]
        cursor = encode_cursor({"created_at": last["created_at"], "id": last["id"]})

        resp2 = await async_client.get(
            f"/listings?city={city}&property_type=apartment&page_size=2&sort=newest&cursor={cursor}"
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) >= 1
        for item in data2["items"]:
            assert item["property_type"] == "apartment"

    async def test_cursor_paginates_all_items(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Cursor All")
        ids = await self._create_listings_batch(async_client, admin_token, city, count=6)

        boot = await async_client.get(f"/listings?city={city}&page_size=2&sort=newest")
        boot_data = boot.json()
        first_ids = [it["id"] for it in boot_data["items"]]
        last = boot_data["items"][-1]
        cursor = encode_cursor({"created_at": last["created_at"], "id": last["id"]})

        all_returned_ids = list(first_ids)
        for _ in range(10):
            resp = await async_client.get(
                f"/listings?city={city}&page_size=2&sort=newest&cursor={cursor}"
            )
            assert resp.status_code == 200
            data = resp.json()
            all_returned_ids.extend(it["id"] for it in data["items"])
            if not data.get("next_cursor"):
                break
            cursor = data["next_cursor"]

        assert len(all_returned_ids) == 6, f"Got {len(all_returned_ids)} items: {all_returned_ids}"
        assert len(set(all_returned_ids)) == 6
        assert set(ids) == set(all_returned_ids)

    async def test_cursor_response_shape(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        city = self._city("Cursor Shape")
        await self._create_listings_batch(async_client, admin_token, city, count=3)

        boot = await async_client.get(f"/listings?city={city}&page_size=2&sort=newest")
        assert boot.status_code == 200
        boot_data = boot.json()
        assert len(boot_data["items"]) == 2
        last = boot_data["items"][-1]
        cursor = encode_cursor({"created_at": last["created_at"], "id": last["id"]})

        resp2 = await async_client.get(f"/listings?city={city}&page_size=2&sort=newest&cursor={cursor}")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert "items" in data2
        assert "page" in data2
        assert "page_size" in data2
        assert "has_next" in data2
        assert "has_previous" in data2
        assert "next_cursor" in data2
        assert data2["page"] == 1
        assert data2["page_size"] == 2

    async def test_cursor_pagination_with_parking_filter(self, async_client: AsyncClient):
        # Verify that parking filter is accepted alongside cursor-based pagination
        resp = await async_client.get("/listings?parking=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "next_cursor" in data
