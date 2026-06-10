from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_actor, get_tenant_context
from app.common.dependencies import get_db_session
from app.common.exceptions import RateLimitExceededError
from app.common.pagination import PaginationRequest
from app.common.rate_limit import check_phase4_rate_limit
from app.common.tenant import TenantContext
from app.viewings.schemas import (
    ViewingSlotCreateRequest,
    ViewingSlotUpdateRequest,
    ViewingSlotResponse,
    PublicViewingSlotResponse,
    ViewingBookingRequest,
    ScheduledViewingResponse,
    PaginatedScheduledViewingsResponse,
    ViewingStatusUpdateRequest,
)
from app.viewings.service import ViewingSlotService, ViewingBookingService

router = APIRouter(prefix="/agency/listings", tags=["Viewing Slots"])


@router.get("/{listing_id}/viewing-slots", response_model=list[ViewingSlotResponse])
async def list_viewing_slots(
    listing_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ViewingSlotService(db, tenant)
    return await svc.list_slots(listing_id)


@router.post("/{listing_id}/viewing-slots", response_model=ViewingSlotResponse, status_code=201)
async def create_viewing_slot(
    listing_id: UUID,
    body: ViewingSlotCreateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ViewingSlotService(db, tenant)
    return await svc.create_slot(listing_id, body.model_dump())


@router.patch("/{listing_id}/viewing-slots/{slot_id}", response_model=ViewingSlotResponse)
async def update_viewing_slot(
    listing_id: UUID,
    slot_id: UUID,
    body: ViewingSlotUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ViewingSlotService(db, tenant)
    return await svc.update_slot(listing_id, slot_id, body.model_dump(exclude_none=True))


@router.delete("/{listing_id}/viewing-slots/{slot_id}", status_code=204)
async def deactivate_viewing_slot(
    listing_id: UUID,
    slot_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ViewingSlotService(db, tenant)
    await svc.deactivate_slot(listing_id, slot_id)


booking_router = APIRouter(tags=["Viewings"])
agency_viewings_router = APIRouter(prefix="/agency/viewings", tags=["Viewings"])


@booking_router.get("/listings/{listing_id}/viewing-slots", response_model=list[PublicViewingSlotResponse])
async def list_public_viewing_slots(
    listing_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    from app.viewings.repository import ViewingSlotRepository

    repo = ViewingSlotRepository(db)
    return await repo.list_active_by_listing(listing_id)


@booking_router.post("/listings/{listing_id}/viewings", response_model=ScheduledViewingResponse, status_code=201)
async def book_viewing(
    listing_id: UUID,
    body: ViewingBookingRequest,
    request: Request,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    identifier = request.client.host if request.client else "unknown"
    if not await check_phase4_rate_limit("viewing_booking", identifier):
        raise RateLimitExceededError(detail="Too many viewing bookings. Please try again later.")

    svc = ViewingBookingService(db)
    return await svc.book_viewing(listing_id, UUID(actor["user_id"]), body.model_dump())


@booking_router.get("/me/viewings", response_model=PaginatedScheduledViewingsResponse)
async def list_my_viewings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = ViewingBookingService(db)
    result = await svc.list_user_viewings(UUID(actor["user_id"]), pp)
    return PaginatedScheduledViewingsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@booking_router.get("/me/viewings/{viewing_id}", response_model=ScheduledViewingResponse)
async def get_my_viewing(
    viewing_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ViewingBookingService(db)
    return await svc.get_user_viewing(viewing_id, UUID(actor["user_id"]))


@agency_viewings_router.get("", response_model=PaginatedScheduledViewingsResponse)
async def list_agency_viewings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = ViewingBookingService(db, tenant)
    result = await svc.list_tenant_viewings(pp)
    return PaginatedScheduledViewingsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@agency_viewings_router.get("/{viewing_id}", response_model=ScheduledViewingResponse)
async def get_agency_viewing(
    viewing_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ViewingBookingService(db, tenant)
    return await svc.get_tenant_viewing(viewing_id)


@agency_viewings_router.patch("/{viewing_id}", response_model=ScheduledViewingResponse)
async def update_viewing_status(
    viewing_id: UUID,
    body: ViewingStatusUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ViewingBookingService(db, tenant)
    return await svc.update_viewing_status(viewing_id, body.status, body.reason)
