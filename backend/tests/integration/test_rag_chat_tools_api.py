"""Integration tests for the RAG chat assistant tool orchestration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str, password: str) -> str:
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


async def _seed_listing(db_session, *, tenant_id, user_id):
    from app.listings.models import Listing

    listing = Listing(
        id=uuid4(),
        agency_tenant_id=tenant_id,
        created_by_user_id=user_id,
        title="Test Listing",
        description="A test listing for tool tests",
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
    return listing


@pytest.mark.anyio
class TestChatToolAugmentation:
    async def test_list_recent_leads_question_returns_lead_summary(
        self, async_client: AsyncClient, agency_admin_user, db_session, test_tenant
    ):
        from app.leads.models import Lead

        user, _ = agency_admin_user
        listing = await _seed_listing(db_session, tenant_id=test_tenant.id, user_id=user.id)

        lead = Lead(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            listing_id=listing.id,
            name="Layla Hassan",
            email="layla@example.com",
            phone="+9613123456",
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
        data = resp.json()
        answer_text = data.get("assistant_message", {}).get("content") or ""
        assert "Layla Hassan" in answer_text or "leads" in answer_text.lower()

    async def test_search_listings_question_returns_listing_summary(
        self, async_client: AsyncClient, agency_admin_user, db_session, test_tenant
    ):
        user, _ = agency_admin_user
        listing = await _seed_listing(
            db_session, tenant_id=test_tenant.id, user_id=user.id,
        )
        listing.title = "Spacious Beirut Loft"
        listing.description = "3 bedroom apartment in Achrafieh"
        listing.bedrooms = 3
        listing.area_size = 150
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        thread_id = await _create_thread(async_client, token)

        with patch(
            "app.rag.service.RagRetrievalService.answer_policy_query",
            new=AsyncMock(return_value=_mock_answer("Here are your listings.")),
        ):
            resp = await async_client.post(
                f"/api/v1/agencies/rag/chat/threads/{thread_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "search listings in Beirut"},
            )
        assert resp.status_code == 200
        data = resp.json()
        answer_text = data.get("assistant_message", {}).get("content") or ""
        assert "listings" in answer_text.lower() or "no" in answer_text.lower()

    async def test_policy_question_does_not_trigger_tools(
        self, async_client: AsyncClient, agency_admin_user
    ):
        user, _ = agency_admin_user
        token = await _login(async_client, user.email, "TestPass123!")
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
        data = resp.json()
        answer_text = data.get("assistant_message", {}).get("content") or ""
        assert "most recent leads" not in answer_text.lower()

    async def test_get_lead_without_id_refuses(
        self, async_client: AsyncClient, agency_admin_user
    ):
        user, _ = agency_admin_user
        token = await _login(async_client, user.email, "TestPass123!")
        thread_id = await _create_thread(async_client, token)

        with patch(
            "app.rag.service.RagRetrievalService.answer_policy_query",
            new=AsyncMock(return_value=_mock_answer("Please specify a lead ID.")),
        ):
            resp = await async_client.post(
                f"/api/v1/agencies/rag/chat/threads/{thread_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "show me lead details"},
            )
        assert resp.status_code == 200
        data = resp.json()
        answer_text = data.get("assistant_message", {}).get("content") or ""
        assert "id" in answer_text.lower() or "specify" in answer_text.lower()
