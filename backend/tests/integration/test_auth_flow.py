import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
class TestAuthFlow:
    async def test_login_with_valid_credentials(self, async_client: AsyncClient, test_user):
        user, password = test_user
        response = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "actor" in data

    async def test_login_with_invalid_credentials(self, async_client: AsyncClient, test_user):
        user, _password = test_user
        response = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": "wrongpassword!",
        })
        assert response.status_code == 401

    async def test_login_with_nonexistent_user(self, async_client: AsyncClient):
        response = await async_client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Test1234!",
        })
        assert response.status_code == 401

    async def test_refresh_with_valid_token(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        refresh_token = login_resp.json()["refresh_token"]

        response = await async_client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_invalid_token(self, async_client: AsyncClient):
        response = await async_client.post("/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert response.status_code == 401

    async def test_refresh_reuse_detected(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        refresh_token = login_resp.json()["refresh_token"]

        await async_client.post("/auth/refresh", json={"refresh_token": refresh_token})
        response = await async_client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401

    async def test_logout(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        refresh_token = login_resp.json()["refresh_token"]
        access_token = login_resp.json()["access_token"]

        response = await async_client.post("/auth/logout", json={
            "refresh_token": refresh_token,
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 204

    async def test_me_returns_actor(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.get("/auth/me", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["actor"]["email"] == user.email

    async def test_me_without_auth(self, async_client: AsyncClient):
        response = await async_client.get("/auth/me")
        assert response.status_code == 401
