import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
class TestAuthFlow:
    async def test_login_sets_httponly_refresh_cookie(self, async_client: AsyncClient, test_user):
        user, password = test_user
        response = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" not in data
        assert data["token_type"] == "bearer"
        assert "actor" in data

        cookies = response.cookies
        assert "akarai_refresh" in cookies

        set_cookie_headers = [h for h in response.headers.get_list("set-cookie") if "akarai_refresh" in h]
        assert len(set_cookie_headers) == 1
        cookie_str = set_cookie_headers[0]
        assert "HttpOnly" in cookie_str
        assert "Path=/" in cookie_str

    async def test_login_sets_csrf_cookie(self, async_client: AsyncClient, test_user):
        user, password = test_user
        response = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert response.status_code == 200

        cookies = response.cookies
        assert "akarai_csrf" in cookies

        set_cookie_headers = [h for h in response.headers.get_list("set-cookie") if "akarai_csrf" in h]
        assert len(set_cookie_headers) == 1
        cookie_str = set_cookie_headers[0]
        assert "HttpOnly" not in cookie_str

    async def test_login_json_does_not_expose_refresh_token(self, async_client: AsyncClient, test_user):
        user, password = test_user
        response = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert response.status_code == 200
        data = response.json()
        assert "refresh_token" not in data

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

    async def test_refresh_with_cookie_and_csrf(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert login_resp.status_code == 200

        csrf_token = login_resp.cookies.get("akarai_csrf")

        response = await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" not in data

        set_cookie_headers = [h for h in response.headers.get_list("set-cookie") if "akarai_refresh" in h]
        assert len(set_cookie_headers) == 1

    async def test_refresh_rotates_cookie(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert login_resp.status_code == 200

        csrf_token = login_resp.cookies.get("akarai_csrf")

        refresh_resp = await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert refresh_resp.status_code == 200

        set_cookie_headers = [h for h in refresh_resp.headers.get_list("set-cookie") if "akarai_refresh" in h]
        assert len(set_cookie_headers) == 1

    async def test_refresh_without_csrf_succeeds(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert login_resp.status_code == 200

        # CSRF is not required for refresh (relies on SameSite cookie)
        response = await async_client.post("/auth/refresh")
        assert response.status_code == 200

    async def test_refresh_without_cookie_fails(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert login_resp.status_code == 200

        csrf_token = login_resp.cookies.get("akarai_csrf")
        async_client.cookies.delete("akarai_refresh")

        response = await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert response.status_code == 401

    async def test_refresh_reuse_detected(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert login_resp.status_code == 200

        csrf_token = login_resp.cookies.get("akarai_csrf")
        original_cookie = login_resp.cookies.get("akarai_refresh")

        await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )

        async_client.cookies.set("akarai_refresh", original_cookie)
        response = await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert response.status_code == 401

    async def test_logout_clears_cookie_and_revokes_session(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.post("/auth/logout", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert response.status_code == 204

        set_cookie_headers = [h for h in response.headers.get_list("set-cookie") if "akarai_refresh" in h]
        assert len(set_cookie_headers) == 1
        cookie_str = set_cookie_headers[0]
        assert "akarai_refresh=" in cookie_str
        assert "Max-Age=0" in cookie_str or "expires=" in cookie_str.lower()

    async def test_logout_clears_csrf_cookie(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]

        response = await async_client.post("/auth/logout", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert response.status_code == 204

        set_cookie_headers = [h for h in response.headers.get_list("set-cookie") if "akarai_csrf" in h]
        assert len(set_cookie_headers) == 1

    async def test_logout_invalidates_refresh_cookie(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        access_token = login_resp.json()["access_token"]
        old_refresh_cookie = login_resp.cookies.get("akarai_refresh")

        await async_client.post("/auth/logout", headers={
            "Authorization": f"Bearer {access_token}",
        })

        csrf_resp = await async_client.get("/auth/csrf-token")
        csrf_token = csrf_resp.cookies.get("akarai_csrf")

        async_client.cookies.set("akarai_refresh", old_refresh_cookie)
        refresh_resp = await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert refresh_resp.status_code == 401

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

    async def test_csrf_token_endpoint(self, async_client: AsyncClient):
        response = await async_client.get("/auth/csrf-token")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data

        set_cookie_headers = [h for h in response.headers.get_list("set-cookie") if "akarai_csrf" in h]
        assert len(set_cookie_headers) == 1
        cookie_str = set_cookie_headers[0]
        assert "HttpOnly" not in cookie_str

    async def test_refresh_with_invalid_csrf_succeeds(self, async_client: AsyncClient, test_user):
        user, password = test_user
        login_resp = await async_client.post("/auth/login", json={
            "email": user.email,
            "password": password,
        })
        assert login_resp.status_code == 200

        # CSRF is not required for refresh (relies on SameSite cookie)
        response = await async_client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": "invalid-csrf-token"},
        )
        assert response.status_code == 200
