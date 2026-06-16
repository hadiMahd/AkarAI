"""Integration tests for the /listings/cities endpoint backed by the cities table."""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.anyio
class TestCitiesEndpoint:
    async def test_cities_returns_ok(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/cities")
        assert resp.status_code == 200

    async def test_cities_returns_list_of_strings(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/cities")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert all(isinstance(c, str) for c in data)

    async def test_cities_contains_beirut(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/cities")
        assert resp.status_code == 200
        assert "Beirut" in resp.json()

    async def test_cities_contains_all_seeded_cities(self, async_client: AsyncClient):
        expected = {"Beirut", "Jounieh", "Tripoli", "Sidon", "Tyre", "Zahle", "Byblos", "Aley"}
        resp = await async_client.get("/listings/cities")
        assert resp.status_code == 200
        returned = set(resp.json())
        assert expected.issubset(returned)

    async def test_cities_is_sorted_alphabetically(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/cities")
        assert resp.status_code == 200
        data = resp.json()
        assert data == sorted(data)

    async def test_cities_does_not_require_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/listings/cities")
        assert resp.status_code == 200

    async def test_cities_does_not_return_inactive(self, db_session: AsyncSession):
        """Verify the cities table itself does not have is_active=False rows from seed."""
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM cities WHERE is_active = false")
        )
        inactive_count = result.scalar()
        assert inactive_count == 0, "Seed should not insert inactive cities"

    async def test_cities_table_exists(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cities')")
        )
        assert result.scalar() is True


@pytest.mark.anyio
class TestCityRepository:
    async def test_list_active_names_returns_strings(self, db_session: AsyncSession):
        from app.cities.repository import CityRepository

        repo = CityRepository(db_session)
        names = await repo.list_active_names()
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)

    async def test_list_active_names_includes_seeded_cities(self, db_session: AsyncSession):
        from app.cities.repository import CityRepository

        repo = CityRepository(db_session)
        names = await repo.list_active_names()
        assert "Beirut" in names
        assert "Jounieh" in names

    async def test_list_active_names_is_sorted(self, db_session: AsyncSession):
        from app.cities.repository import CityRepository

        repo = CityRepository(db_session)
        names = await repo.list_active_names()
        assert names == sorted(names)

    async def test_list_active_returns_city_objects(self, db_session: AsyncSession):
        from app.cities.repository import CityRepository
        from app.cities.models import City

        repo = CityRepository(db_session)
        cities = await repo.list_active()
        assert isinstance(cities, list)
        assert all(isinstance(c, City) for c in cities)
        assert all(c.is_active for c in cities)

    async def test_cities_migration_seeded_eight_records(self, db_session: AsyncSession):
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM cities WHERE country = 'Lebanon' AND is_active = true")
        )
        count = result.scalar()
        assert count >= 8, f"Expected at least 8 Lebanese cities, got {count}"
