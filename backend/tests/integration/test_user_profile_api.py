import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestUserProfileAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_get_my_profile(self, async_client: AsyncClient):
        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.get("/me/profile", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@akarai.test"
        assert "is_complete_for_leads" in data
        assert "missing_fields" in data

    async def test_update_my_profile(self, async_client: AsyncClient):
        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.put(
            "/me/profile",
            json={"name": "Updated Name", "phone": "+96170000000"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"
        assert data["phone"] == "+96170000000"
        assert data["is_complete_for_leads"] is True

    async def test_update_my_profile_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.put("/me/profile", json={"name": "Updated Name"})
        assert resp.status_code == 401
