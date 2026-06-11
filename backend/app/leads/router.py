from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_actor, get_rls_db_session, get_tenant_context
from app.common.dependencies import get_db_session, pagination_params
from app.common.exceptions import RateLimitExceededError
from app.common.pagination import PaginationRequest
from app.common.rate_limit import check_phase4_rate_limit
from app.common.tenant import TenantContext
from app.leads.schemas import (
    LeadInquiryRequest,
    LeadResponse,
    PaginatedLeadsResponse,
    LeadStatusUpdateRequest,
    LeadReviewRequest,
    ReviewedLeadRecordResponse,
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
    return await svc.create_inquiry(listing_id, UUID(actor["user_id"]), body.model_dump())


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
    return PaginatedLeadsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@agency_router.get("", response_model=PaginatedLeadsResponse)
async def list_agency_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reviewed: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = LeadService(db, tenant)
    result = await svc.list_tenant_leads(pp, reviewed=reviewed, status=status)
    return PaginatedLeadsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@agency_router.get("/{lead_id}", response_model=LeadResponse)
async def get_agency_lead(
    lead_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = LeadService(db, tenant)
    return await svc.get_lead(lead_id)


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
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = LeadService(db, tenant)
    return await svc.review_lead(lead_id, tenant.actor_id, body.model_dump())
