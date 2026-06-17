from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_actor, get_rls_db_session, get_tenant_context
from app.common.config import settings
from app.common.dependencies import get_db_session, pagination_params
from app.common.exceptions import ForbiddenError, RateLimitExceededError
from app.common.rls import apply_rls_context_to_session
from app.common.pagination import PaginationRequest
from app.common.rate_limit import check_phase4_rate_limit, check_lead_processing_rate_limit
from app.common.tenant import TenantContext
from app.leads.schemas import (
    LeadInquiryRequest,
    LeadResponse,
    PaginatedLeadsResponse,
    LeadStatusUpdateRequest,
    LeadReviewRequest,
    ReviewedLeadRecordResponse,
    LeadClassificationCallbackRequest,
    LeadClassificationCallbackResponse,
    LeadSpamResultResponse,
    LeadLevelResultResponse,
)
from app.leads.service import LeadService

router = APIRouter(tags=["Leads"])
agency_router = APIRouter(prefix="/agency/leads", tags=["Leads"])


@router.post("/listings/{listing_id}/inquiries", response_model=LeadResponse, status_code=201)
async def submit_inquiry(
    listing_id: UUID,
    body: LeadInquiryRequest,
    request: Request,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    identifier = request.client.host if request.client else "unknown"
    if not await check_phase4_rate_limit("inquiry", identifier):
        raise RateLimitExceededError(detail="Too many inquiries. Please try again later.")

    svc = LeadService(db)
    lead = await svc.create_inquiry(listing_id, UUID(actor["user_id"]), body.model_dump())
    return _enrich_lead_response(lead)


@router.get("/me/inquiries", response_model=PaginatedLeadsResponse)
async def list_my_inquiries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = LeadService(db)
    result = await svc.list_user_inquiries(UUID(actor["user_id"]), pp)
    return await _enrich_paginated_response(db, result)


@agency_router.get("", response_model=PaginatedLeadsResponse)
async def list_agency_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reviewed: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    spam_label: Optional[str] = Query(None, description="Filter by spam classification: 'spam' or 'not_spam'"),
    processing_status: Optional[str] = Query(None, description="Filter by processing state: 'pending', 'completed'"),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = LeadService(db, tenant)
    result = await svc.list_tenant_leads(pp, reviewed=reviewed, status=status, spam_label=spam_label, processing_status=processing_status)
    return await _enrich_paginated_response(db, result, svc)


@agency_router.get("/{lead_id}", response_model=LeadResponse)
async def get_agency_lead(
    lead_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = LeadService(db, tenant)
    lead = await svc.get_lead(lead_id)
    return await _enrich_lead_with_classification(db, lead)


@agency_router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead_status(
    lead_id: UUID,
    body: LeadStatusUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = LeadService(db, tenant)
    return await svc.update_lead_status(lead_id, body.status)


@agency_router.post("/{lead_id}/review", response_model=ReviewedLeadRecordResponse, status_code=201)
async def review_lead(
    lead_id: UUID,
    body: LeadReviewRequest,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = LeadService(db, tenant)
    result = await svc.review_lead(lead_id, tenant.actor_id, body.model_dump())
    # Audit log the review action
    from app.audit.repository import AuditLogRepository
    from app.audit.models import AuditLog
    from datetime import datetime, timezone
    audit_repo = AuditLogRepository(db)
    audit_repo.session.add(AuditLog(
        action="lead_processing.reviewed",
        result="success",
        actor_user_id=tenant.actor_id,
        tenant_id=tenant.tenant_id,
        request_id=None,
        ip_address=request.client.host if request.client else None,
        event_metadata={
            "lead_id": str(lead_id),
            "outcome": body.outcome,
        },
        created_at=datetime.now(timezone.utc),
    ))
    await db.flush()
    return result


# ── Internal callback endpoint for lead model service ──

internal_router = APIRouter(prefix="/api/v1/internal/leads", tags=["Internal Lead Processing"])


async def get_internal_db_session(
    db: AsyncSession = Depends(get_db_session),
) -> AsyncSession:
    """Session with platform-admin RLS context for internal service callbacks."""
    await apply_rls_context_to_session(db, is_platform_admin=True)
    return db


@internal_router.post("/classification-callback", response_model=LeadClassificationCallbackResponse)
async def classification_callback(
    body: LeadClassificationCallbackRequest,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_internal_db_session),
):
    # Validate callback auth token
    expected_token = f"Bearer {settings.lead_model_service_callback_token}"
    if not settings.lead_model_service_callback_token or authorization != expected_token:
        raise ForbiddenError(detail="Invalid callback authorization")

    svc = LeadService(db)
    idempotency_key = f"callback_{body.lead_id}_{body.stage}_r{body.retry_count}"

    if body.stage == "spam":
        result = await svc.process_spam_callback(
            lead_id=body.lead_id,
            tenant_id=body.tenant_id,
            status=body.status,
            label=body.label,
            score=body.score,
            details=body.details,
            retry_count=body.retry_count,
            idempotency_key=idempotency_key,
        )
        return LeadClassificationCallbackResponse(
            lead_id=body.lead_id,
            stage="spam",
            status=result.status,
            label=result.label,
        )
    else:
        result = await svc.process_level_callback(
            lead_id=body.lead_id,
            tenant_id=body.tenant_id,
            status=body.status,
            level=body.label,
            score=body.score,
            details=body.details,
            retry_count=body.retry_count,
            idempotency_key=idempotency_key,
        )
        return LeadClassificationCallbackResponse(
            lead_id=body.lead_id,
            stage="level",
            status=result.status,
            label=result.level,
        )


# ── Classification result endpoints ──

@agency_router.get("/{lead_id}/spam-result", response_model=LeadSpamResultResponse)
async def get_lead_spam_result(
    lead_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = LeadService(db, tenant)
    result = await svc.get_spam_result(lead_id)
    if result is None:
        from app.common.exceptions import NotFoundError
        raise NotFoundError(detail="Spam result not found")
    return result


@agency_router.get("/{lead_id}/level-result", response_model=LeadLevelResultResponse)
async def get_lead_level_result(
    lead_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = LeadService(db, tenant)
    result = await svc.get_level_result(lead_id)
    if result is None:
        from app.common.exceptions import NotFoundError
        raise NotFoundError(detail="Level result not found")
    return result


# ── Response enrichment helpers ──

def _enrich_lead_response(lead) -> LeadResponse:
    return LeadResponse.model_validate(lead)


async def _enrich_lead_with_classification(db: AsyncSession, lead) -> LeadResponse:
    svc = LeadService(db)
    spam = await svc.get_spam_result(lead.id)
    level = await svc.get_level_result(lead.id)
    data = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "spam_label": spam.label if spam else None,
        "spam_score": float(spam.score) if spam and spam.score else None,
        "lead_level": level.level if level else None,
        "level_score": float(level.score) if level and level.score else None,
    }
    return LeadResponse(**data)


async def _enrich_paginated_response(db: AsyncSession, result, svc: LeadService | None = None) -> PaginatedLeadsResponse:
    if svc is None:
        svc = LeadService(db)
    enriched = []
    for lead in result.items:
        enriched.append(await _enrich_lead_with_classification(db, lead))
    return PaginatedLeadsResponse(
        items=enriched,
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )
