"""RBAC tests for the platform admin dashboard access gate.

The dashboard enforces a TWO-stage gate:
1. ``platform_admin`` role (existing platform auth)
2. ``platform:dashboard_read`` permission (new dedicated gate)

The tests verify:
- platform_admin WITH the permission succeeds
- platform_admin WITHOUT the permission is rejected
- agency_admin is rejected at the role check
- support_employee is rejected
- unauthenticated is rejected
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session


PLATFORM_ADMIN_EMAIL = "platform.admin@akarai.test"
AGENCY_ADMIN_EMAIL = "agency.admin@akarai.test"
SUPPORT_EMAIL = "support@akarai.test"


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _perm_id(db_session, key: str) -> uuid.UUID | None:
    """Lookup a permission id by key. Returns None if missing."""
    result = await db_session.execute(
        text("SELECT id FROM permissions WHERE key = :k"), {"k": key}
    )
    return result.scalar()


async def _apply_platform_context(session) -> None:
    if not session.in_transaction():
        await session.begin()
    await apply_rls_context_to_session(
        session,
        role="platform_admin",
        is_platform_admin=True,
    )


@pytest.mark.asyncio
class TestPlatformDashboardAccess:
    @pytest.mark.integration
    async def test_unauthenticated_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/platform/dashboard/insights")
        assert resp.status_code == 401

    @pytest.mark.integration
    async def test_agency_admin_returns_403(self, async_client: AsyncClient):
        token = await _login(async_client, AGENCY_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/dashboard/insights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.integration
    async def test_support_employee_returns_403(self, async_client: AsyncClient):
        token = await _login(async_client, SUPPORT_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/dashboard/insights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.integration
    async def test_platform_admin_without_dashboard_permission_is_rejected(
        self, async_client: AsyncClient
    ):
        async with async_session_factory() as session:
            await _apply_platform_context(session)
            pid = await _perm_id(session, "platform:dashboard_read")
            if pid is None:
                pytest.skip("platform:dashboard_read permission not seeded")

            role_result = await session.execute(
                text("SELECT id FROM roles WHERE slug = 'platform_admin'")
            )
            role_id = role_result.scalar()
            assert role_id is not None

            await session.execute(
                text("DELETE FROM role_permissions WHERE role_id = :r AND permission_id = :p"),
                {"r": role_id, "p": pid},
            )
            await session.commit()

            try:
                token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
                resp = await async_client.get(
                    "/api/v1/platform/dashboard/insights",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert resp.status_code == 403
            finally:
                await _apply_platform_context(session)
                await session.execute(
                    text(
                        "INSERT INTO role_permissions (role_id, permission_id, created_at) "
                        "VALUES (:r, :p, :now) ON CONFLICT DO NOTHING"
                    ),
                    {
                        "r": role_id,
                        "p": pid,
                        "now": datetime.now(timezone.utc),
                    },
                )
                await session.commit()

    @pytest.mark.integration
    async def test_platform_admin_with_dashboard_permission_succeeds(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/dashboard/insights",
            params={"range_preset": "last_30_days"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
