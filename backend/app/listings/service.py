from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.domain import (
    LISTING_STATUS_TRANSITIONS,
    VALID_LISTING_STATUSES,
    LISTING_STATUS_ACTIVE,
    LISTING_STATUS_INACTIVE,
    LISTING_STATUS_ARCHIVED,
)
from app.common.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.tenant import TenantContext, require_tenant, ensure_tenant_match
from app.common.cache import invalidate_listing_search_cache
from app.common.events import write_domain_event_log
from app.listings.models import Listing, ListingPhotoMetadata
from app.listings.repository import ListingRepository, ListingPhotoRepository


class ListingService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._repo = ListingRepository(session, tenant)
        self._photo_repo = ListingPhotoRepository(session, tenant)

    async def list_tenant_listings(self, pagination: PaginationRequest) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def get_listing(self, listing_id: UUID) -> Listing:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)
        return listing

    async def create_listing(self, data: dict) -> Listing:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot create listings")

        listing = Listing(
            agency_tenant_id=ctx.tenant_id,
            title=data["title"],
            description=data.get("description"),
            property_type=data.get("property_type"),
            listing_purpose=data.get("listing_purpose"),
            price=data.get("price"),
            currency=data.get("currency"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            area_size=data.get("area_size"),
            area_unit=data.get("area_unit"),
            furnishing=data.get("furnishing"),
            location_text=data.get("location_text"),
            address=data.get("address"),
            city=data.get("city"),
            country=data.get("country"),
            status=data.get("status", "inactive"),
            created_by_user_id=ctx.actor_id,
        )
        if listing.status not in VALID_LISTING_STATUSES:
            raise ValidationError(detail=f"Invalid listing status: {listing.status}")
        listing = await self._repo.create(listing)
        await write_domain_event_log(
            self._session, "listing.created",
            aggregate_type="listing", aggregate_id=str(listing.id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"title": listing.title, "status": listing.status},
        )
        return listing

    async def update_listing(self, listing_id: UUID, data: dict) -> Listing:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)

        for field in (
            "title",
            "description",
            "property_type",
            "listing_purpose",
            "price",
            "currency",
            "bedrooms",
            "bathrooms",
            "area_size",
            "area_unit",
            "furnishing",
            "location_text",
            "address",
            "city",
            "country",
        ):
            if field in data and data[field] is not None:
                setattr(listing, field, data[field])

        if "status" in data and data["status"] is not None:
            new_status = data["status"]
            if new_status not in VALID_LISTING_STATUSES:
                raise ValidationError(detail=f"Invalid listing status: {new_status}")
            allowed = LISTING_STATUS_TRANSITIONS.get(listing.status, [])
            if new_status not in allowed:
                raise ValidationError(
                    detail=f"Cannot transition from '{listing.status}' to '{new_status}'"
                )
            listing.status = new_status
            if new_status == LISTING_STATUS_ARCHIVED:
                listing.archived_at = datetime.now(timezone.utc)

        listing.updated_by_user_id = ctx.actor_id
        await self._session.flush()
        await invalidate_listing_search_cache(str(listing_id))
        await write_domain_event_log(
            self._session, "listing.updated",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"status": listing.status},
        )
        return listing

    async def archive_listing(self, listing_id: UUID) -> None:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)
        if listing.status == LISTING_STATUS_ARCHIVED:
            return

        listing.status = LISTING_STATUS_ARCHIVED
        listing.archived_at = datetime.now(timezone.utc)
        listing.updated_by_user_id = ctx.actor_id
        await self._session.flush()
        await invalidate_listing_search_cache(str(listing_id))
        await write_domain_event_log(
            self._session, "listing.archived",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
        )

    async def list_photos(self, listing_id: UUID) -> list[ListingPhotoMetadata]:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)
        return await self._photo_repo.list_by_listing(listing_id)

    async def create_photo(self, listing_id: UUID, data: dict) -> ListingPhotoMetadata:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)

        order = data.get("display_order", 0)
        if order == 0:
            max_order = await self._photo_repo.get_max_display_order(listing_id)
            order = max_order + 1

        photo = ListingPhotoMetadata(
            listing_id=listing_id,
            agency_tenant_id=ctx.tenant_id,
            object_key=data["object_key"],
            caption=data.get("caption"),
            alt_text=data.get("alt_text"),
            display_order=order,
            status="active",
        )
        photo = await self._photo_repo.create(photo)
        await write_domain_event_log(
            self._session, "listing.photo_added",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"photo_id": str(photo.id)},
        )
        return photo

    async def update_photo(self, listing_id: UUID, photo_id: UUID, data: dict) -> ListingPhotoMetadata:
        ctx = require_tenant(self._tenant)
        photo = await self._photo_repo.get_by_id(photo_id)
        if photo is None:
            raise NotFoundError(detail="Photo metadata not found")
        if str(photo.listing_id) != str(listing_id):
            raise NotFoundError(detail="Photo not found for this listing")
        ensure_tenant_match(self._tenant, photo.agency_tenant_id)

        if "caption" in data:
            photo.caption = data["caption"]
        if "alt_text" in data:
            photo.alt_text = data["alt_text"]
        if "display_order" in data and data["display_order"] is not None:
            photo.display_order = data["display_order"]

        await self._session.flush()
        await write_domain_event_log(
            self._session, "listing.photo_updated",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=photo.agency_tenant_id, actor_user_id=ctx.actor_id,
            payload={"photo_id": str(photo_id)},
        )
        return photo

    async def remove_photo(self, listing_id: UUID, photo_id: UUID) -> None:
        ctx = require_tenant(self._tenant)
        photo = await self._photo_repo.get_by_id(photo_id)
        if photo is None:
            raise NotFoundError(detail="Photo metadata not found")
        if str(photo.listing_id) != str(listing_id):
            raise NotFoundError(detail="Photo not found for this listing")
        ensure_tenant_match(self._tenant, photo.agency_tenant_id)

        photo.status = "removed"
        await self._session.flush()
        await write_domain_event_log(
            self._session, "listing.photo_removed",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=photo.agency_tenant_id, actor_user_id=ctx.actor_id,
            payload={"photo_id": str(photo_id)},
        )
