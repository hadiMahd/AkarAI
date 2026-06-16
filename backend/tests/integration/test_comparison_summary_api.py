"""Integration tests for the user comparison summary endpoint
/api/v1/me/comparison-summary.
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


async def _seed_listing(
    db_session, *, tenant_id, title, city, price, beds, area, area_unit
):
    """Create a public listing for the comparison summary to fetch."""
    from app.listings.models import Listing

    listing = Listing(
        id=uuid4(),
        agency_tenant_id=tenant_id,
        title=title,
        description=f"{title} description",
        property_type="apartment",
        listing_purpose="rent",
        price=price,
        currency="USD",
        bedrooms=beds,
        area_size=area,
        area_unit=area_unit,
        city=city,
        country="Lebanon",
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


@pytest.mark.anyio
class TestComparisonSummaryEndpoint:
    async def test_summary_returns_2_to_4_listings(
        self, async_client: AsyncClient, test_user, db_session, test_tenant
    ):
        from app.ai.guardrails import GuardrailedGenerationResult

        user, _ = test_user
        l1 = await _seed_listing(
            db_session,
            tenant_id=test_tenant.id,
            title="Beirut Loft",
            city="Beirut",
            price=1500,
            beds=2,
            area=120,
            area_unit="sqm",
        )
        l2 = await _seed_listing(
            db_session,
            tenant_id=test_tenant.id,
            title="Hamra Studio",
            city="Beirut",
            price=900,
            beds=1,
            area=55,
            area_unit="sqm",
        )
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")

        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"summary": "Both are Beirut rentals.", "key_differences": ["Beirut Loft is 2BR, Hamra Studio is 1BR"], "best_fit_notes": ["Loft for families"]}',
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
        data = resp.json()
        assert "summary" in data or "job_id" in data

    async def test_summary_rejects_one_listing(
        self, async_client: AsyncClient, test_user
    ):
        token = await _login(async_client, test_user[0].email, "TestPass123!")
        resp = await async_client.post(
            "/api/v1/me/comparison-summary",
            headers={"Authorization": f"Bearer {token}"},
            json={"listing_ids": [str(uuid4())]},
        )
        assert resp.status_code in (400, 422)

    async def test_summary_rejects_five_listings(
        self, async_client: AsyncClient, test_user
    ):
        token = await _login(async_client, test_user[0].email, "TestPass123!")
        resp = await async_client.post(
            "/api/v1/me/comparison-summary",
            headers={"Authorization": f"Bearer {token}"},
            json={"listing_ids": [str(uuid4()) for _ in range(5)]},
        )
        assert resp.status_code in (400, 422)

    async def test_summary_dedupes_listing_ids(
        self, async_client: AsyncClient, test_user, db_session, test_tenant
    ):
        from app.ai.guardrails import GuardrailedGenerationResult

        user, _ = test_user
        l1 = await _seed_listing(
            db_session,
            tenant_id=test_tenant.id,
            title="Loft",
            city="Beirut",
            price=1000,
            beds=2,
            area=80,
            area_unit="sqm",
        )
        l2 = await _seed_listing(
            db_session,
            tenant_id=test_tenant.id,
            title="Studio",
            city="Beirut",
            price=600,
            beds=1,
            area=40,
            area_unit="sqm",
        )
        await db_session.commit()

        token = await _login(async_client, user.email, "TestPass123!")
        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"summary": "ok", "key_differences": [], "best_fit_notes": []}',
                    guardrail_status="passed",
                    blocked_reason=None,
                    generation_provider="test",
                )
            ),
        ):
            resp = await async_client.post(
                "/api/v1/me/comparison-summary",
                headers={"Authorization": f"Bearer {token}"},
                json={"listing_ids": [str(l1.id), str(l1.id), str(l2.id)]},
            )
        assert resp.status_code == 200

    async def test_summary_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/me/comparison-summary",
            json={"listing_ids": [str(uuid4()), str(uuid4())]},
        )
        assert resp.status_code in (401, 403)
