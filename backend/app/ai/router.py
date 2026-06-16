"""Agency AI Workflows router.

This router exposes the Phase 12 endpoints:
- POST   /api/v1/agencies/listings/spec-sheet-extractions (queue OCR)
- GET    /api/v1/agencies/ai/jobs/{job_id}                  (job status)
- POST   /api/v1/agencies/listings/draft                    (listing draft)
- POST   /api/v1/agencies/leads/{lead_id}/reply-draft       (lead reply)
- POST   /api/v1/me/comparison-summary                     (user comparison)

The new endpoints reuse the existing auth, tenant, and rate limit
dependencies from the rest of the backend.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import (
    AgencyAIJobRead,
    ComparisonSummaryRequest,
    ComparisonSummaryResponse,
    LeadReplyDraftRequest,
    LeadReplyDraftResponse,
    ListingDraftRequest,
    ListingDraftResponse,
    SpecExtractionJobAcceptedResponse,
    SpecExtractionResultResponse,
)
from app.ai.service import AgencyAIService
from app.auth.dependencies import (
    get_current_actor,
    get_rls_db_session,
    get_tenant_context,
    require_role,
)
from app.common.exceptions import (
    AppException,
    ForbiddenError,
    NotFoundError,
    RateLimitExceededError,
)
from app.common.rate_limit import check_agency_ai_rate_limit
from app.common.tenant import TenantContext

logger = logging.getLogger(__name__)


# ── Agency-side AI router ─────────────────────────────────────────

agency_ai_router = APIRouter(prefix="/api/v1/agencies", tags=["Agency AI"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@agency_ai_router.post(
    "/listings/spec-sheet-extractions",
    response_model=SpecExtractionJobAcceptedResponse,
    status_code=202,
)
async def queue_spec_sheet_extraction(
    request: Request,
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    if not await check_agency_ai_rate_limit(
        "agency_ai:ocr",
        _client_ip(request),
        max_requests=None,
        window_seconds=None,
    ):
        raise RateLimitExceededError(detail="Too many OCR requests. Please try again later.")

    file_bytes = await file.read()
    service = AgencyAIService(db, tenant)
    return await service.queue_spec_extraction(
        file_bytes=file_bytes,
        filename=file.filename or "spec-sheet.pdf",
        content_type=file.content_type,
    )


@agency_ai_router.get(
    "/listings/spec-sheet-extractions/{job_id}",
    response_model=SpecExtractionResultResponse,
)
async def get_spec_sheet_extraction(
    job_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = AgencyAIService(db, tenant)
    return await service.get_spec_extraction(job_id)


@agency_ai_router.post(
    "/listings/draft",
    response_model=ListingDraftResponse,
)
async def generate_listing_draft(
    request: Request,
    body: ListingDraftRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    if not await check_agency_ai_rate_limit(
        "agency_ai:listing_draft",
        _client_ip(request),
        max_requests=None,
        window_seconds=None,
    ):
        raise RateLimitExceededError(
            detail="Too many listing draft requests. Please try again later."
        )

    service = AgencyAIService(db, tenant)
    return await service.queue_listing_draft(
        listing_context=body.listing_context,
        extracted_specs=body.extracted_specs.model_dump() if body.extracted_specs else None,
        listing_id=body.listing_id,
    )


@agency_ai_router.post(
    "/leads/{lead_id}/reply-draft",
    response_model=LeadReplyDraftResponse,
)
async def generate_lead_reply_draft(
    request: Request,
    lead_id: UUID,
    body: LeadReplyDraftRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    if not await check_agency_ai_rate_limit(
        "agency_ai:lead_reply",
        _client_ip(request),
        max_requests=None,
        window_seconds=None,
    ):
        raise RateLimitExceededError(
            detail="Too many reply draft requests. Please try again later."
        )

    service = AgencyAIService(db, tenant)
    return await service.queue_lead_reply_draft(lead_id=lead_id, channel=body.channel)


@agency_ai_router.get(
    "/ai/jobs/{job_id}",
    response_model=AgencyAIJobRead,
)
async def get_agency_ai_job(
    job_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = AgencyAIService(db, tenant)
    job = await service.get_job(job_id)
    return AgencyAIJobRead.model_validate(job)


# ── User-side AI router (comparison summary) ──────────────────────

user_ai_router = APIRouter(prefix="/api/v1/me", tags=["User AI"])


@user_ai_router.post(
    "/comparison-summary",
    response_model=ComparisonSummaryResponse,
)
async def create_comparison_summary(
    request: Request,
    body: ComparisonSummaryRequest,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    if not await check_agency_ai_rate_limit(
        "agency_ai:comparison_summary",
        _client_ip(request),
        max_requests=None,
        window_seconds=None,
    ):
        raise RateLimitExceededError(
            detail="Too many comparison summary requests. Please try again later."
        )

    user_id = UUID(actor["user_id"])
    service = AgencyAIService(db)
    return await service.queue_comparison_summary(
        user_id=user_id,
        listing_ids=body.listing_ids,
    )
