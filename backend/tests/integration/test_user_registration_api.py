import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import text, select

from app.users.models import User
from app.common.database import async_session_factory


async def _get_user_by_email(email: str) -> User | None:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def _delete_user_by_email(email: str) -> None:
    async with async_session_factory() as session:
        await session.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email},
        )
        await session.commit()


@pytest.mark.anyio
class TestUserRegistrationAPI:
    async def test_register_new_user_success(self, async_client: AsyncClient):
        unique_id = str(uuid.uuid4())[:8]
        email = f"newuser_{unique_id}@akarai.test"
        payload = {
            "email": email,
            "password": "Test1234!",
            "name": "New User",
        }

        try:
            response = await async_client.post("/auth/register", json=payload)

            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" not in data
            assert "actor" in data
            assert data["actor"]["email"] == email

            cookies = response.cookies
            assert "akarai_refresh" in cookies

            user = await _get_user_by_email(email)
            assert user is not None
            assert user.name == "New User"
            assert user.is_active is True
        finally:
            await _delete_user_by_email(email)

    async def test_register_duplicate_email_fails(self, async_client: AsyncClient):
        unique_id = str(uuid.uuid4())[:8]
        email = f"duplicate_{unique_id}@akarai.test"
        payload = {
            "email": email,
            "password": "Test1234!",
            "name": "First User",
        }

        try:
            response1 = await async_client.post("/auth/register", json=payload)
            assert response1.status_code == 201

            payload["name"] = "Second User"
            response2 = await async_client.post("/auth/register", json=payload)
            assert response2.status_code == 409
            assert "already exists" in response2.json()["detail"].lower()
        finally:
            await _delete_user_by_email(email)

    async def test_register_invalid_email_fails(self, async_client: AsyncClient):
        payload = {
            "email": "not-an-email",
            "password": "Test1234!",
            "name": "Test User",
        }

        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_weak_password_fails(self, async_client: AsyncClient):
        payload = {
            "email": f"weak_{str(uuid.uuid4())[:8]}@akarai.test",
            "password": "short",
            "name": "Test User",
        }

        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_missing_name_fails(self, async_client: AsyncClient):
        payload = {
            "email": f"noname_{str(uuid.uuid4())[:8]}@akarai.test",
            "password": "Test1234!",
        }

        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_sets_refresh_cookie(self, async_client: AsyncClient):
        unique_id = str(uuid.uuid4())[:8]
        email = f"tokens_{unique_id}@akarai.test"
        payload = {
            "email": email,
            "password": "Test1234!",
            "name": "Token User",
        }

        try:
            response = await async_client.post("/auth/register", json=payload)
            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" not in data
            assert data["token_type"] == "bearer"

            cookies = response.cookies
            assert "akarai_refresh" in cookies
        finally:
            await _delete_user_by_email(email)

    async def test_register_user_can_login_after_registration(self, async_client: AsyncClient):
        unique_id = str(uuid.uuid4())[:8]
        email = f"login_{unique_id}@akarai.test"
        register_payload = {
            "email": email,
            "password": "Test1234!",
            "name": "Login User",
        }

        try:
            register_response = await async_client.post("/auth/register", json=register_payload)
            assert register_response.status_code == 201

            login_payload = {
                "email": email,
                "password": "Test1234!",
            }

            login_response = await async_client.post("/auth/login", json=login_payload)
            assert login_response.status_code == 200
            assert "access_token" in login_response.json()
        finally:
            await _delete_user_by_email(email)
