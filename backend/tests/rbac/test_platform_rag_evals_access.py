from __future__ import annotations

from datetime import datetime, timezone

import pytest
from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session
from httpx import AsyncClient
from sqlalchemy import text

PLATFORM_ADMIN_EMAIL = "platform.admin@akarai.test"
SUPPORT_EMAIL = "support@akarai.test"


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    response = await client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def _perm_id(db_session, key: str):
    result = await db_session.execute(
        text("SELECT id FROM permissions WHERE key = :key"), {"key": key}
    )
    return result.scalar()


async def _apply_platform_context(session) -> None:
    if not session.in_transaction():
        await session.begin()
    await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)


@pytest.mark.asyncio
class TestPlatformRagEvalAccess:
    @pytest.mark.integration
    async def test_support_employee_returns_403(self, async_client: AsyncClient):
        token = await _login(async_client, SUPPORT_EMAIL)
        response = await async_client.get(
            "/api/v1/platform/rag-evals/runs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.integration
    async def test_platform_admin_without_dashboard_permission_is_rejected(
        self, async_client: AsyncClient
    ):
        async with async_session_factory() as session:
            await _apply_platform_context(session)
            permission_id = await _perm_id(session, "platform:dashboard_read")
            if permission_id is None:
                pytest.skip("platform:dashboard_read permission not seeded")

            role_result = await session.execute(
                text("SELECT id FROM roles WHERE slug = 'platform_admin'")
            )
            role_id = role_result.scalar()
            assert role_id is not None

            await session.execute(
                text(
                    "DELETE FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            )
            await session.commit()

            try:
                token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
                response = await async_client.get(
                    "/api/v1/platform/rag-evals/runs",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert response.status_code == 403
            finally:
                await _apply_platform_context(session)
                await session.execute(
                    text(
                        "INSERT INTO role_permissions (role_id, permission_id, created_at) "
                        "VALUES (:role_id, :permission_id, :created_at) ON CONFLICT DO NOTHING"
                    ),
                    {
                        "role_id": role_id,
                        "permission_id": permission_id,
                        "created_at": datetime.now(timezone.utc),
                    },
                )
                await session.commit()
