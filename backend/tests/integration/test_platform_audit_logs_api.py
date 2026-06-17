"""Integration tests for ``/api/v1/platform/audit-logs``."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


PLATFORM_ADMIN_EMAIL = "platform.admin@akarai.test"
AGENCY_ADMIN_EMAIL = "agency.admin@akarai.test"


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.anyio
class TestPlatformAuditLogsAPI:
    @pytest.mark.integration
    async def test_platform_admin_can_list_audit_logs(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/audit-logs",
            params={"page": 1, "page_size": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        for key in (
            "items",
            "page",
            "page_size",
            "total",
            "has_next",
            "has_previous",
        ):
            assert key in data
        for item in data["items"]:
            assert "id" in item
            assert "created_at" in item
            assert "actor_role" in item
            assert "feature_area" in item
            assert "action" in item
            assert "result" in item
            assert "redacted_metadata" in item

    @pytest.mark.integration
    async def test_agency_admin_is_forbidden(self, async_client: AsyncClient):
        token = await _login(async_client, AGENCY_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/audit-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.integration
    async def test_unauthenticated_is_rejected(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/platform/audit-logs")
        assert resp.status_code == 401

    @pytest.mark.integration
    async def test_pagination_bounds(self, async_client: AsyncClient):
        token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
        # page_size > max should be rejected (422)
        resp = await async_client.get(
            "/api/v1/platform/audit-logs",
            params={"page_size": 999},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_audit_log_with_secret_metadata_is_redacted(
        self, async_client: AsyncClient, db_session
    ):
        from app.audit.models import AuditLog

        now = datetime.now(timezone.utc)
        log = AuditLog(
            id=uuid.uuid4(),
            request_id=str(uuid.uuid4()),
            action="rag.document_uploaded",
            resource_type="rag_document",
            result="success",
            event_metadata={
                "actor_role": "agency_admin",
                "required_permission": "rag:read",
                "password": "supersecret_should_be_dropped",
                "ip_address_truncated": "10.0.0.7",
            },
            created_at=now,
        )
        db_session.add(log)
        await db_session.commit()
        try:
            token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
            resp = await async_client.get(
                "/api/v1/platform/audit-logs",
                params={"page_size": 50},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            items = resp.json()["items"]
            match = next(
                (
                    item
                    for item in items
                    if item["id"] == str(log.id)
                ),
                None,
            )
            assert match is not None
            assert match["feature_area"] == "rag"
            meta = match["redacted_metadata"]
            assert "password" not in meta
            assert meta.get("actor_role") in {"agency_admin", "unknown", None}
        finally:
            await db_session.delete(log)
            await db_session.commit()

    @pytest.mark.integration
    async def test_filter_by_feature_area(self, async_client: AsyncClient, db_session):
        from app.audit.models import AuditLog

        now = datetime.now(timezone.utc)
        auth_log = AuditLog(
            id=uuid.uuid4(),
            action="auth.sign_in.success",
            result="success",
            created_at=now,
        )
        listing_log = AuditLog(
            id=uuid.uuid4(),
            action="listing.created",
            result="success",
            created_at=now,
        )
        db_session.add_all([auth_log, listing_log])
        await db_session.commit()
        try:
            token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
            resp = await async_client.get(
                "/api/v1/platform/audit-logs",
                params={"feature_area": "auth", "page_size": 50},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            items = resp.json()["items"]
            for item in items:
                assert item["feature_area"] == "auth"
        finally:
            for log in (auth_log, listing_log):
                await db_session.delete(log)
            await db_session.commit()
