import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.notifications.models import Notification


@pytest.mark.anyio
class TestNotificationAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_list_notifications_empty(self, async_client: AsyncClient):
        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.get("/notifications", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_list_notifications_with_data(self, async_client: AsyncClient, db_session):
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM users WHERE email = 'user@akarai.test'"))
        user_id = result.fetchone()[0]

        n = Notification(
            recipient_user_id=user_id,
            channel="platform",
            template_key="test_api",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.get("/notifications", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_get_notification(self, async_client: AsyncClient, db_session):
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM users WHERE email = 'user@akarai.test'"))
        user_id = result.fetchone()[0]

        n = Notification(
            recipient_user_id=user_id,
            channel="platform",
            template_key="test_get_api",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.get(
            f"/notifications/{n.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(n.id)

    async def test_mark_notification_read(self, async_client: AsyncClient, db_session):
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM users WHERE email = 'user@akarai.test'"))
        user_id = result.fetchone()[0]

        n = Notification(
            recipient_user_id=user_id,
            channel="platform",
            template_key="test_read_api",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            f"/notifications/{n.id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "read"
        assert resp.json()["read_at"] is not None

    async def test_dismiss_notification(self, async_client: AsyncClient, db_session):
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM users WHERE email = 'user@akarai.test'"))
        user_id = result.fetchone()[0]

        n = Notification(
            recipient_user_id=user_id,
            channel="platform",
            template_key="test_dismiss_api",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            f"/notifications/{n.id}/dismiss",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "dismissed"

    async def test_notification_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/notifications")
        assert resp.status_code == 401

    async def test_get_notification_not_found(self, async_client: AsyncClient):
        token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.get(
            f"/notifications/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


@pytest.mark.anyio
class TestSearchLogAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_list_search_logs(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/search-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_search_logs_pagination(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/search-logs?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_search_logs_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/agency/search-logs")
        assert resp.status_code == 401


@pytest.mark.anyio
class TestDomainLogAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_list_domain_logs(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/domain-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_domain_logs_pagination(self, async_client: AsyncClient):
        token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/domain-logs?page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_domain_logs_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/agency/domain-logs")
        assert resp.status_code == 401
