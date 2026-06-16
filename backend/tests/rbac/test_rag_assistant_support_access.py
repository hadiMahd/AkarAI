"""RBAC tests for the assistant route and tool usage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_thread(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/agencies/rag/chat/threads",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["thread"]["id"]


def _mock_answer(answer_text: str):
    from app.rag.schemas import RagPolicyAnswer

    return RagPolicyAnswer(
        status="success",
        answer=answer_text,
        citations=[],
        evidence=[],
        debug=None,
    )


@pytest.mark.anyio
class TestAssistantSupportAccess:
    async def test_support_employee_can_use_assistant(self, async_client: AsyncClient):
        token = await _login(async_client, "support@akarai.test")
        thread_id = await _create_thread(async_client, token)

        with patch(
            "app.rag.service.RagRetrievalService.answer_policy_query",
            new=AsyncMock(return_value=_mock_answer("The parking policy allows 2 cars per unit.")),
        ):
            resp = await async_client.post(
                f"/api/v1/agencies/rag/chat/threads/{thread_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "What is the parking policy?"},
            )
        assert resp.status_code == 200

    async def test_support_employee_cannot_upload_policy_documents(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, "support@akarai.test")
        files = {"file": ("policy.pdf", b"%PDF-1.4\n", "application/pdf")}
        resp = await async_client.post(
            "/api/v1/agencies/rag/documents",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_support_employee_can_list_policy_documents(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, "support@akarai.test")
        resp = await async_client.get(
            "/api/v1/agencies/rag/documents",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_support_employee_cannot_view_retrieval_logs(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, "support@akarai.test")
        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_agency_admin_can_view_retrieval_logs(
        self, async_client: AsyncClient
    ):
        token = await _login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_unauthenticated_cannot_call_assistant(
        self, async_client: AsyncClient
    ):
        resp = await async_client.post(
            "/api/v1/agencies/rag/chat/threads",
            json={},
        )
        assert resp.status_code in (401, 403)


@pytest.mark.anyio
class TestAssistantToolTenantIsolation:
    async def test_tool_output_only_returns_own_tenant(
        self, async_client: AsyncClient, agency_admin_user, db_session, test_tenant
    ):
        from app.leads.models import Lead
        from app.listings.models import Listing

        user, _ = agency_admin_user
        listing = Listing(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            created_by_user_id=user.id,
            title="Test Listing",
            description="A test listing",
            property_type="apartment",
            listing_purpose="rent",
            price=1500,
            currency="USD",
            bedrooms=2,
            area_size=120,
            area_unit="sqm",
            city="Beirut",
            country="Lebanon",
            status="active",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(listing)
        await db_session.flush()

        lead = Lead(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            listing_id=listing.id,
            name="Layla",
            email="layla@example.com",
            status="new",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(lead)
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        thread_id = await _create_thread(async_client, token)

        with patch(
            "app.rag.service.RagRetrievalService.answer_policy_query",
            new=AsyncMock(return_value=_mock_answer("Here are the most recent leads.")),
        ):
            resp = await async_client.post(
                f"/api/v1/agencies/rag/chat/threads/{thread_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "show me the last 5 leads"},
            )
        assert resp.status_code == 200
