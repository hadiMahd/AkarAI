import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
class TestPasswordReset:
    async def test_password_reset_with_valid_current_password(self, async_client: AsyncClient, test_user):
        user, password = test_user

        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.post("/auth/password-reset", json={
            "current_password": password,
            "new_password": "NewTest5678!",
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 204

    async def test_password_reset_with_wrong_current_password(self, async_client: AsyncClient, test_user):
        user, password = test_user

        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.post("/auth/password-reset", json={
            "current_password": "WrongPassword!",
            "new_password": "NewTest5678!",
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 400

    async def test_password_reset_without_auth(self, async_client: AsyncClient):
        response = await async_client.post("/auth/password-reset", json={
            "current_password": "Test1234!",
            "new_password": "NewTest5678!",
        })
        assert response.status_code == 401

    async def test_password_reset_invalidates_sessions(self, async_client: AsyncClient, test_user):
        user, password = test_user

        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]
        csrf_token = login_resp.cookies.get("akarai_csrf")

        await async_client.post("/auth/password-reset", json={
            "current_password": password,
            "new_password": "NewTest5678!",
        }, headers={"Authorization": f"Bearer {access_token}"})

        refresh_resp = await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert refresh_resp.status_code == 401
