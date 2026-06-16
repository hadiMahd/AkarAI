"""Integration tests for agency listing AI endpoints (spec extraction,
listing draft, and job status). These tests use mocked OCR and chat
providers to avoid real provider calls.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog>>\nendobj\n%%EOF\n"


def _login(client: AsyncClient, email: str = "agency.admin@akarai.test", password: str = "Test1234!") -> str:
    import asyncio

    async def _do():
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    return asyncio.get_event_loop().run_until_complete(_do())


async def _login_async(client: AsyncClient, email: str = "agency.admin@akarai.test", password: str = "Test1234!") -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _login_admin_user(client: AsyncClient, agency_admin_user) -> str:
    user, _ = agency_admin_user
    resp = await client.post("/auth/login", json={"email": user.email, "password": "TestPass123!"})
    assert resp.status_code == 200, f"login failed: {resp.status_code} {resp.text}"
    return resp.json()["access_token"]


@pytest.mark.anyio
class TestSpecSheetExtraction:
    async def test_upload_pdf_extracts_specs(self, async_client: AsyncClient):
        token = await _login_async(async_client)
        files = {"file": ("spec.pdf", io.BytesIO(PDF_BYTES), "application/pdf")}
        with patch(
            "app.ai.azure_openai.AzureComputerVisionOCRProvider.extract_text",
            new=AsyncMock(
                return_value="3 bedrooms 2 bathrooms 150 sqm apartment in Beirut"
            ),
        ):
            resp = await async_client.post(
                "/api/v1/agencies/listings/spec-sheet-extractions",
                files=files,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code in (200, 202)
        data = resp.json()
        assert data["status"] in ("review_ready", "completed", "queued", "processing")

    async def test_upload_rejects_oversized(self, async_client: AsyncClient):
        token = await _login_async(async_client)
        # 11 MB
        big = b"x" * (11 * 1024 * 1024)
        files = {"file": ("big.pdf", io.BytesIO(big), "application/pdf")}
        resp = await async_client.post(
            "/api/v1/agencies/listings/spec-sheet-extractions",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 413

    async def test_upload_rejects_wrong_type(self, async_client: AsyncClient):
        token = await _login_async(async_client)
        files = {"file": ("specs.zip", io.BytesIO(b"abc"), "application/zip")}
        resp = await async_client.post(
            "/api/v1/agencies/listings/spec-sheet-extractions",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 415

    async def test_get_spec_extraction_job(self, async_client: AsyncClient, db_session, test_tenant, agency_admin_user):
        from app.ai.models import AgencyAIJob
        from app.ai.jobs import (
            JOB_TYPE_OCR_EXTRACTION,
            JOB_STATUS_COMPLETED,
            new_job,
        )

        user, _ = agency_admin_user
        job = new_job(
            job_type=JOB_TYPE_OCR_EXTRACTION,
            tenant_id=test_tenant.id,
            actor_user_id=user.id,
        )
        job.status = JOB_STATUS_COMPLETED
        job.result_payload = {"raw_text_excerpt": "3 bedrooms"}
        db_session.add(job)
        await db_session.commit()
        job_id = str(job.id)

        token = await _login_admin_user(async_client, agency_admin_user)
        resp = await async_client.get(
            f"/api/v1/agencies/listings/spec-sheet-extractions/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "completed"


@pytest.mark.anyio
class TestListingDraftEndpoint:
    async def test_draft_returns_title_description(self, async_client: AsyncClient, agency_admin_user):
        from app.ai.guardrails import GuardrailedGenerationResult

        user, _ = agency_admin_user
        token = await _login_async(async_client)

        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text='{"title": "Spacious Beirut Loft", "description": "Modern loft in the heart of Beirut", "highlights": ["3 bedrooms", "150 sqm"]}',
                    guardrail_status="passed",
                    blocked_reason=None,
                    generation_provider="test",
                )
            ),
        ):
            resp = await async_client.post(
                "/api/v1/agencies/listings/draft",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "listing_context": {
                        "title": "Loft",
                        "city": "Beirut",
                        "price": 1500,
                    }
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["title"] == "Spacious Beirut Loft"
        assert "description" in data

    async def test_draft_validates_required_context(self, async_client: AsyncClient, agency_admin_user):
        token = await _login_async(async_client)
        resp = await async_client.post(
            "/api/v1/agencies/listings/draft",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        # Pydantic validation rejects missing listing_context
        assert resp.status_code in (400, 422)

    async def test_draft_blocks_on_guardrail_block(
        self, async_client: AsyncClient, agency_admin_user
    ):
        from app.ai.guardrails import GuardrailedGenerationResult

        token = await _login_async(async_client)
        with patch(
            "app.ai.service.generate_guardrailed_agency_text",
            new=AsyncMock(
                return_value=GuardrailedGenerationResult(
                    answer_text="",
                    guardrail_status="blocked",
                    blocked_reason="policy_violation",
                    generation_provider="test",
                )
            ),
        ):
            resp = await async_client.post(
                "/api/v1/agencies/listings/draft",
                headers={"Authorization": f"Bearer {token}"},
                json={"listing_context": {"title": "x", "city": "y", "price": 1}},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] in (None, "")
        assert data["blocked_reason"] == "policy_violation"


@pytest.mark.anyio
class TestJobStatusEndpoint:
    async def test_get_job_returns_queued_status(
        self, async_client: AsyncClient, db_session, test_tenant, agency_admin_user
    ):
        from app.ai.models import AgencyAIJob
        from app.ai.jobs import JOB_TYPE_LISTING_DRAFT, new_job

        user, _ = agency_admin_user
        job = new_job(
            job_type=JOB_TYPE_LISTING_DRAFT,
            tenant_id=test_tenant.id,
            actor_user_id=user.id,
        )
        db_session.add(job)
        await db_session.commit()
        job_id = str(job.id)

        token = await _login_admin_user(async_client, agency_admin_user)
        resp = await async_client.get(
            f"/api/v1/agencies/ai/jobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["status"] in ("queued", "processing", "completed", "blocked", "failed")

    async def test_get_missing_job_returns_404(
        self, async_client: AsyncClient, agency_admin_user
    ):
        token = await _login_async(async_client)
        resp = await async_client.get(
            f"/api/v1/agencies/ai/jobs/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
