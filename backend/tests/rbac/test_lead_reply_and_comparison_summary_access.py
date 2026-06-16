"""RBAC tests for lead reply draft and user comparison summary access:
agency employees can draft lead replies; signed-in users can request
comparison summaries; cross-tenant access is blocked.
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


async def _seed_listing(db_session, *, tenant_id, user_id):
    from app.listings.models import Listing

    listing = Listing(
        id=uuid4(),
        agency_tenant_id=tenant_id,
        created_by_user_id=user_id,
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
    return listing


@pytest.mark.anyio
class TestLeadReplyAccess:
    async def test_agency_admin_can_draft_reply(
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
            name="Test",
            status="new",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(lead)
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"subject": "s", "body": "b"}',
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

    async def test_support_employee_can_draft_reply(
        self, async_client: AsyncClient, support_user, db_session, test_tenant
    ):
        from app.leads.models import Lead
        from app.ai.guardrails import GuardrailedGenerationResult

        user, _ = support_user
        listing = await _seed_listing(db_session, tenant_id=test_tenant.id, user_id=user.id)

        lead = Lead(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            listing_id=listing.id,
            name="Test",
            status="new",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(lead)
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"subject": "s", "body": "b"}',
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

    async def test_cross_tenant_lead_returns_404(
        self, async_client: AsyncClient, agency_admin_user, db_session, test_tenant
    ):
        """Verify that an agency admin in another tenant cannot draft
        replies against a lead belonging to test_tenant."""
        from app.leads.models import Lead

        user, _ = agency_admin_user
        listing = await _seed_listing(db_session, tenant_id=test_tenant.id, user_id=user.id)

        lead = Lead(
            id=uuid4(),
            agency_tenant_id=test_tenant.id,
            listing_id=listing.id,
            name="Test",
            status="new",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(lead)
        await db_session.commit()

        # Admin from the seed tenant logs in; the lead belongs to test_tenant,
        # so the endpoint should return 404 (not found = tenant-isolated).
        token = await _login(async_client, "agency.admin@akarai.test")
        resp = await async_client.post(
            f"/api/v1/agencies/leads/{lead.id}/reply-draft",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": "email"},
        )
        assert resp.status_code == 404


@pytest.mark.anyio
class TestComparisonSummaryAccess:
    async def test_signed_in_user_can_request_summary(
        self, async_client: AsyncClient, test_user, db_session, test_tenant
    ):
        from app.ai.guardrails import GuardrailedGenerationResult

        user = test_user[0]
        l1 = await _seed_listing(db_session, tenant_id=test_tenant.id, user_id=user.id)
        l2 = await _seed_listing(
            db_session, tenant_id=test_tenant.id, user_id=user.id, 
        )
        l2.title = "Second Listing"
        l2.price = 900
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"summary": "test", "key_differences": [], "best_fit_notes": []}',
                    guardrail_status="passed",
                    blocked_reason=None,
                    generation_provider="test",
                )
            ),
        ):
            resp = await async_client.post(
                "/api/v1/me/comparison-summary",
                headers={"Authorization": f"Bearer {token}"},
                json={"listing_ids": [str(l1.id), str(l2.id)]},
            )
        assert resp.status_code == 200

    async def test_summary_rejects_invalid_listing_count(
        self, async_client: AsyncClient, test_user
    ):
        token = await _login(async_client, test_user[0].email, "TestPass123!")
        resp = await async_client.post(
            "/api/v1/me/comparison-summary",
            headers={"Authorization": f"Bearer {token}"},
            json={"listing_ids": [str(uuid4())]},
        )
        assert resp.status_code == 422
