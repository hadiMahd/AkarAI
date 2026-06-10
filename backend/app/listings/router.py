from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_actor,
    get_optional_current_actor,
    get_rls_db_session,
    get_tenant_context,
)
from app.common.cache import cache_get, cache_set, LISTING_SEARCH_NAMESPACE
from app.common.dependencies import get_db_session
from app.common.domain import MAX_COMPARISON_ITEMS
from app.common.exceptions import NotFoundError, ForbiddenError, ConflictError, RateLimitExceededError
from app.common.pagination import PaginationRequest
from app.common.rate_limit import check_phase4_rate_limit
from app.common.tenant import TenantContext
from app.search.service import SearchService
from app.listings.schemas import (
    ListingCreateRequest,
    ListingUpdateRequest,
    ListingResponse,
    PaginatedListingsResponse,
    PublicListingResponse,
    PaginatedPublicListingsResponse,
    ListingPhotoMetadataCreateRequest,
    ListingPhotoMetadataUpdateRequest,
    ListingPhotoMetadataResponse,
    SavedListingResponse,
    SavedListingWithDetailsResponse,
    PaginatedSavedListingsResponse,
    PaginatedSavedListingsWithDetailsResponse,
    ComparisonSessionCreateRequest,
    ComparisonSessionUpdateRequest,
    ComparisonSessionResponse,
    PaginatedComparisonSessionsResponse,
    ComparisonItemCreateRequest,
    ComparisonItemResponse,
)
from app.listings.service import ListingService

router = APIRouter(prefix="/agency/listings", tags=["Agency Listings"])


@router.get("", response_model=PaginatedListingsResponse)
async def list_tenant_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = ListingService(db, tenant)
    result = await svc.list_tenant_listings(pp)
    return PaginatedListingsResponse(
        items=result.items,
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing(
    body: ListingCreateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    return await svc.create_listing(body.model_dump())


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    return await svc.get_listing(listing_id)


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: UUID,
    body: ListingUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    return await svc.update_listing(listing_id, body.model_dump(exclude_none=True))


@router.delete("/{listing_id}", status_code=204)
async def archive_listing(
    listing_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    await svc.archive_listing(listing_id)


@router.get("/{listing_id}/photos", response_model=list[ListingPhotoMetadataResponse])
async def list_photos(
    listing_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    return await svc.list_photos(listing_id)


@router.post("/{listing_id}/photos", response_model=ListingPhotoMetadataResponse, status_code=201)
async def create_photo(
    listing_id: UUID,
    body: ListingPhotoMetadataCreateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    return await svc.create_photo(listing_id, body.model_dump())


@router.patch("/{listing_id}/photos/{photo_id}", response_model=ListingPhotoMetadataResponse)
async def update_photo(
    listing_id: UUID,
    photo_id: UUID,
    body: ListingPhotoMetadataUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    return await svc.update_photo(listing_id, photo_id, body.model_dump(exclude_none=True))


@router.delete("/{listing_id}/photos/{photo_id}", status_code=204)
async def remove_photo(
    listing_id: UUID,
    photo_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ListingService(db, tenant)
    await svc.remove_photo(listing_id, photo_id)


# ── Public listing search routes ────────────────────────────────────────────

public_router = APIRouter(prefix="/listings", tags=["Public Listings"])


@public_router.get("", response_model=PaginatedPublicListingsResponse)
async def public_search_listings(
    request: Request,
    location: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[int] = Query(None),
    property_type: Optional[str] = Query(None),
    listing_purpose: Optional[str] = Query(None),
    furnishing: Optional[str] = Query(None),
    min_area_size: Optional[float] = Query(None),
    max_area_size: Optional[float] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    actor: Optional[dict] = Depends(get_optional_current_actor),
):
    client_ip = request.client.host if request.client else "unknown"
    allowed = await check_phase4_rate_limit("search", client_ip)
    if not allowed:
        raise RateLimitExceededError(detail="Too many search requests. Please try again later.")

    from app.listings.query_service import ListingQueryService
    from app.listings.models import Listing

    filters = {
        "location": location, "min_price": min_price, "max_price": max_price,
        "bedrooms": bedrooms, "bathrooms": bathrooms, "property_type": property_type,
        "listing_purpose": listing_purpose, "furnishing": furnishing,
        "min_area_size": min_area_size, "max_area_size": max_area_size,
        "sort": sort, "page": page, "page_size": page_size,
    }
    cache_key = f"search:{hash(frozenset({k: v for k, v in filters.items() if v is not None}.items()))}"

    if page == 1:
        cached = await cache_get(LISTING_SEARCH_NAMESPACE, cache_key)
        if cached is not None and "items" in cached:
            from app.listings.schemas import PaginatedPublicListingsResponse as PLR
            return PLR(**cached)

    q = ListingQueryService.build_public_search_query(
        location=location, min_price=min_price, max_price=max_price,
        bedrooms=bedrooms, bathrooms=bathrooms, property_type=property_type,
        listing_purpose=listing_purpose, furnishing=furnishing,
        min_area_size=min_area_size, max_area_size=max_area_size, sort=sort,
    )

    count_q = select(func.count()).select_from(q.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    offset = (page - 1) * page_size
    paginated_q = q.offset(offset).limit(page_size)
    result = await db.execute(paginated_q)
    items = list(result.scalars().all())

    has_next = (page * page_size) < total
    response_data = PaginatedPublicListingsResponse(
        items=items, page=page, page_size=page_size,
        total=total, has_next=has_next, has_previous=page > 1,
    )

    if page == 1:
        serializable = response_data.model_dump(mode="json")
        await cache_set(LISTING_SEARCH_NAMESPACE, cache_key, serializable, ttl=120)

    search_svc = SearchService(db)
    await search_svc.log_search_event({
        "user_id": UUID(actor["user_id"]) if actor else None,
        "filters": filters,
        "sort": sort,
        "result_count": total,
    })

    return response_data


@public_router.get("/{listing_id}", response_model=PublicListingResponse)
async def public_get_listing(
    listing_id: UUID,
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import ListingRepository

    cached = await cache_get(LISTING_SEARCH_NAMESPACE, f"detail:{listing_id}")
    if cached is not None and "id" in cached:
        from app.listings.schemas import PublicListingResponse as PLR
        return PLR(**cached)

    repo = ListingRepository(db)
    listing = await repo.get_by_id(listing_id)
    if listing is None or listing.status != "active":
        raise NotFoundError(detail="Listing not found")

    serializable = PublicListingResponse.model_validate(listing).model_dump(mode="json")
    await cache_set(LISTING_SEARCH_NAMESPACE, f"detail:{listing_id}", serializable, ttl=300)
    return listing


# ── Saved listings routes ───────────────────────────────────────────────────

saved_router = APIRouter(prefix="/me/saved-listings", tags=["Saved Listings"])


@saved_router.get("", response_model=PaginatedSavedListingsResponse)
async def list_saved_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import SavedListingRepository

    repo = SavedListingRepository(db)
    user_id = UUID(actor["user_id"])
    items, total = await repo.list_by_user(
        user_id, offset=(page - 1) * page_size, limit=page_size,
    )
    return PaginatedSavedListingsResponse(
        items=items, page=page, page_size=page_size,
        total=total, has_next=(page * page_size) < total, has_previous=page > 1,
    )


@saved_router.get("/with-details", response_model=PaginatedSavedListingsWithDetailsResponse)
async def list_saved_listings_with_details(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import SavedListingRepository

    repo = SavedListingRepository(db)
    user_id = UUID(actor["user_id"])
    rows, total = await repo.list_by_user_with_details(
        user_id, offset=(page - 1) * page_size, limit=page_size,
    )
    items = []
    for row in rows:
        saved = row.saved
        listing = row.listing
        items.append(
            SavedListingWithDetailsResponse(
                id=saved.id,
                user_id=saved.user_id,
                listing_id=saved.listing_id,
                created_at=saved.created_at,
                deleted_at=saved.deleted_at,
                listing=PublicListingResponse.model_validate(listing),
            )
        )
    return PaginatedSavedListingsWithDetailsResponse(
        items=items, page=page, page_size=page_size,
        total=total, has_next=(page * page_size) < total, has_previous=page > 1,
    )


@saved_router.put("/{listing_id}", response_model=SavedListingResponse)
async def save_listing(
    listing_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.models import SavedListing
    from app.listings.repository import SavedListingRepository, ListingRepository

    user_id = UUID(actor["user_id"])
    saved_repo = SavedListingRepository(db)
    existing = await saved_repo.get_by_user_and_listing(user_id, listing_id)
    if existing:
        return existing

    listing_repo = ListingRepository(db)
    listing = await listing_repo.get_by_id(listing_id)
    if listing is None or listing.status != "active":
        raise NotFoundError(detail="Listing not found or not active")

    saved = SavedListing(user_id=user_id, listing_id=listing_id)
    saved = await saved_repo.create(saved)
    return saved


@saved_router.delete("/{listing_id}", status_code=204)
async def unsave_listing(
    listing_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import SavedListingRepository

    user_id = UUID(actor["user_id"])
    saved_repo = SavedListingRepository(db)
    saved = await saved_repo.get_by_user_and_listing(user_id, listing_id)
    if saved:
        saved.deleted_at = datetime.now(timezone.utc)
        await db.flush()


# ── Comparison routes ───────────────────────────────────────────────────────

comparison_router = APIRouter(prefix="/me/comparison-sessions", tags=["Comparisons"])


@comparison_router.get("", response_model=PaginatedComparisonSessionsResponse)
async def list_comparison_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import ComparisonRepository

    repo = ComparisonRepository(db)
    user_id = UUID(actor["user_id"])
    items, total = await repo.list_sessions_by_user(
        user_id, offset=(page - 1) * page_size, limit=page_size,
    )
    return PaginatedComparisonSessionsResponse(
        items=items, page=page, page_size=page_size,
        total=total, has_next=(page * page_size) < total, has_previous=page > 1,
    )


@comparison_router.post("", response_model=ComparisonSessionResponse, status_code=201)
async def create_comparison_session(
    body: ComparisonSessionCreateRequest,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.models import ComparisonSession
    from app.listings.repository import ComparisonRepository

    repo = ComparisonRepository(db)
    session = ComparisonSession(user_id=UUID(actor["user_id"]), name=body.name)
    return await repo.create_session(session)


@comparison_router.get("/{session_id}", response_model=ComparisonSessionResponse)
async def get_comparison_session(
    session_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import ComparisonRepository

    repo = ComparisonRepository(db)
    session = await repo.get_session_by_id(session_id)
    if session is None or session.deleted_at is not None:
        raise NotFoundError(detail="Comparison session not found")
    if str(session.user_id) != actor["user_id"]:
        raise ForbiddenError(detail="Not your comparison session")
    return session


@comparison_router.patch("/{session_id}", response_model=ComparisonSessionResponse)
async def update_comparison_session(
    session_id: UUID,
    body: ComparisonSessionUpdateRequest,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import ComparisonRepository

    repo = ComparisonRepository(db)
    session = await repo.get_session_by_id(session_id)
    if session is None or session.deleted_at is not None:
        raise NotFoundError(detail="Comparison session not found")
    if str(session.user_id) != actor["user_id"]:
        raise ForbiddenError(detail="Not your comparison session")
    if body.name is not None:
        session.name = body.name
    await db.flush()
    return session


@comparison_router.delete("/{session_id}", status_code=204)
async def delete_comparison_session(
    session_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    from app.listings.repository import ComparisonRepository

    repo = ComparisonRepository(db)
    session = await repo.get_session_by_id(session_id)
    if session is None:
        raise NotFoundError(detail="Comparison session not found")
    if str(session.user_id) != actor["user_id"]:
        raise ForbiddenError(detail="Not your comparison session")
    session.deleted_at = datetime.now(timezone.utc)
    await db.flush()


@comparison_router.post("/{session_id}/items", response_model=ComparisonItemResponse, status_code=201)
async def add_comparison_item(
    session_id: UUID,
    body: ComparisonItemCreateRequest,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    from app.listings.models import ComparisonItem
    from app.listings.repository import ComparisonRepository

    repo = ComparisonRepository(db)
    session = await repo.get_session_by_id(session_id)
    if session is None or session.deleted_at is not None:
        raise NotFoundError(detail="Comparison session not found")
    if str(session.user_id) != actor["user_id"]:
        raise ForbiddenError(detail="Not your comparison session")

    existing = await repo.get_item(session_id, body.listing_id)
    if existing:
        return existing

    count = await repo.get_item_count(session_id)
    if count >= MAX_COMPARISON_ITEMS:
        raise ConflictError(detail="Comparison session already has the maximum number of items")

    item = ComparisonItem(
        comparison_session_id=session_id,
        listing_id=body.listing_id,
        position=count,
    )
    return await repo.create_item(item)


@comparison_router.delete("/{session_id}/items/{listing_id}", status_code=204)
async def remove_comparison_item(
    session_id: UUID,
    listing_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    from app.listings.repository import ComparisonRepository

    repo = ComparisonRepository(db)
    session = await repo.get_session_by_id(session_id)
    if session is None:
        raise NotFoundError(detail="Comparison session not found")
    if str(session.user_id) != actor["user_id"]:
        raise ForbiddenError(detail="Not your comparison session")

    item = await repo.get_item(session_id, listing_id)
    if item:
        await repo.remove_item(item)
