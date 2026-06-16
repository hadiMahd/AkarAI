"""Integration tests for the lead reply draft endpoint under the
/api/v1/agencies/leads/{lead_id}/reply-draft route.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _seed_listing(db_session, *, tenant_id, user_id, title="Test Listing"):
    from app.listings.models import Listing

    listing = Listing(
        id=uuid4(),
        agency_tenant_id=tenant_id,
        created_by_user_id=user_id,
        title=title,
        description=f"{title} description",
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
class TestLeadReplyDraftEndpoint:
    async def test_draft_email_channel_returns_subject_and_body(
        self, async_client: AsyncClient, agency_admin_user, db_session, test_tenant
    ):
        from app.leads.models import Lead
        from app.ai.guardrails import GuardrailedGenerationResult

        user, _ = agency_admin_user
        listing = await _seed_listing(db_session, tenant_id=test_tenant.id, user_id=user.id)

        lead = Lead(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            listing_id=listing.id,
            name="Karim Saad",
            email="karim@example.com",
            phone="+9617000000",
            status="new",
            message="I'm interested in the Achrafieh loft",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(lead)
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")

        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"subject": "Re: Your inquiry", "body": "Hi Karim, thank you for your interest..."}',
                    guardrail_status="passed",
                    blocked_reason=None,
                    generation_provider="test",
                )
            ),
        ):
            resp = await async_client.post(
                f"/api/v1/agencies/leads/{lead.id}/reply-draft",
                headers={"Authorization": f"Bearer {token}"},
                json={"channel": "email"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["channel"] == "email"
        assert data["subject"] == "Re: Your inquiry"
        assert "Karim" in (data.get("body") or "")

    async def test_draft_whatsapp_channel_returns_body_only(
        self, async_client: AsyncClient, agency_admin_user, db_session, test_tenant
    ):
        from app.leads.models import Lead
        from app.ai.guardrails import GuardrailedGenerationResult

        user, _ = agency_admin_user
        listing = await _seed_listing(db_session, tenant_id=test_tenant.id, user_id=user.id)

        lead = Lead(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            listing_id=listing.id,
            name="Maya",
            email=None,
            phone="+9617111111",
            status="contacted",
            message="Quick question",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(lead)
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"body": "Hi Maya, yes the loft is still available!"}',
                    guardrail_status="passed",
                    blocked_reason=None,
                    generation_provider="test",
                )
            ),
        ):
            resp = await async_client.post(
                f"/api/v1/agencies/leads/{lead.id}/reply-draft",
                headers={"Authorization": f"Bearer {token}"},
                json={"channel": "whatsapp"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["channel"] == "whatsapp"
        assert data["body"] is not None

    async def test_draft_rejects_unknown_channel(
        self, async_client: AsyncClient, agency_admin_user, db_session, test_tenant
    ):
        from app.leads.models import Lead

        user, _ = agency_admin_user
        listing = await _seed_listing(db_session, tenant_id=test_tenant.id, user_id=user.id)

        lead = Lead(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            listing_id=listing.id,
            name="X",
            status="new",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(lead)
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        resp = await async_client.post(
            f"/api/v1/agencies/leads/{lead.id}/reply-draft",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": "sms"},
        )
        assert resp.status_code in (400, 422)

    async def test_draft_404_for_missing_lead(
        self, async_client: AsyncClient, agency_admin_user
    ):
        token = await _login(async_client, agency_admin_user[0].email, "TestPass123!")
        resp = await async_client.post(
            f"/api/v1/agencies/leads/{uuid4()}/reply-draft",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": "email"},
        )
        assert resp.status_code == 404
