import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestAgencyCorePagination:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_list_employees_pagination_contract(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/employees?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert "has_previous" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_list_employees_pagination_page_2(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/employees?page=2&page_size=5", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    async def test_list_employees_pagination_has_previous(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/employees?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_previous"] is False

        resp = await async_client.get("/agencies/me/employees?page=2&page_size=5", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_previous"] is True

    async def test_list_listings_pagination_contract(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agency/listings?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert "has_previous" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_list_listings_pagination_page_2(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agency/listings?page=2&page_size=5", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    async def test_list_listings_pagination_has_previous(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agency/listings?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_previous"] is False

        resp = await async_client.get("/agency/listings?page=2&page_size=5", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_previous"] is True

    async def test_pagination_default_values(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 20

    async def test_pagination_max_page_size(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get("/agencies/me/employees?page_size=100", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 100
