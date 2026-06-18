from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError, ForbiddenError, ValidationError, ConflictError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.rls import apply_rls_context_to_session
from app.common.tenant import TenantContext, require_tenant, ensure_tenant_match
from app.common.events import write_domain_event_log
from app.viewings.models import ListingViewingSlot, ScheduledViewing, ScheduledViewingStatusHistory
from app.viewings.repository import ViewingSlotRepository, ScheduledViewingRepository, ViewingStatusHistoryRepository
from app.listings.models import Listing
from app.listings.repository import ListingRepository
from app.listings.service import build_thumbnail_map

_MIN_SLOT_LEAD_TIME = timedelta(minutes=5)


class ViewingSlotService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._repo = ViewingSlotRepository(session, tenant)
        self._listing_repo = ListingRepository(session, tenant)

    async def list_slots(self, listing_id: UUID) -> list[ListingViewingSlot]:
        ctx = require_tenant(self._tenant)
        listing = await self._listing_repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)
        return await self._repo.list_by_listing(listing_id)

    async def create_slot(self, listing_id: UUID, data: dict) -> ListingViewingSlot:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot create viewing slots")

        listing = await self._listing_repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)

        starts_at = data["starts_at"]
        ends_at = data["ends_at"]
        if starts_at >= ends_at:
            raise ValidationError(detail="ends_at must be after starts_at")
        self._validate_future_slot_start(starts_at)

        slot = ListingViewingSlot(
            listing_id=listing_id,
            agency_tenant_id=ctx.tenant_id,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=data.get("capacity", 1),
            reserved_count=0,
            status="active",
            created_by_user_id=ctx.actor_id,
        )
        slot = await self._repo.create(slot)
        await write_domain_event_log(
            self._session, "listing.viewing_slot_created",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"slot_id": str(slot.id)},
        )
        return slot

    async def update_slot(self, listing_id: UUID, slot_id: UUID, data: dict) -> ListingViewingSlot:
        ctx = require_tenant(self._tenant)
        slot = await self._repo.get_by_id(slot_id)
        if slot is None:
            raise NotFoundError(detail="Viewing slot not found")
        if str(slot.listing_id) != str(listing_id):
            raise NotFoundError(detail="Slot not found for this listing")
        ensure_tenant_match(self._tenant, slot.agency_tenant_id)

        if "starts_at" in data and data["starts_at"] is not None:
            slot.starts_at = data["starts_at"]
        if "ends_at" in data and data["ends_at"] is not None:
            slot.ends_at = data["ends_at"]
        if "capacity" in data and data["capacity"] is not None:
            slot.capacity = data["capacity"]
        if "status" in data and data["status"] is not None:
            slot.status = data["status"]

        if slot.starts_at >= slot.ends_at:
            raise ValidationError(detail="ends_at must be after starts_at")
        self._validate_future_slot_start(slot.starts_at)

        await self._session.flush()
        await write_domain_event_log(
            self._session, "listing.viewing_slot_updated",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"slot_id": str(slot_id)},
        )
        return slot

    async def deactivate_slot(self, listing_id: UUID, slot_id: UUID) -> None:
        ctx = require_tenant(self._tenant)
        slot = await self._repo.get_by_id(slot_id)
        if slot is None:
            raise NotFoundError(detail="Viewing slot not found")
        if str(slot.listing_id) != str(listing_id):
            raise NotFoundError(detail="Slot not found for this listing")
        ensure_tenant_match(self._tenant, slot.agency_tenant_id)

        slot.status = "inactive"
        await self._session.flush()
        await write_domain_event_log(
            self._session, "listing.viewing_slot_deactivated",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"slot_id": str(slot_id)},
        )

    def _validate_future_slot_start(self, starts_at: datetime) -> None:
        starts_at_utc = starts_at.astimezone(timezone.utc)
        minimum_start = datetime.now(timezone.utc) + _MIN_SLOT_LEAD_TIME
        if starts_at_utc < minimum_start:
            raise ValidationError(
                detail="Viewing slot start time must be at least 5 minutes in the future."
            )


class ViewingBookingService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._slot_repo = ViewingSlotRepository(session, tenant)
        self._viewing_repo = ScheduledViewingRepository(session, tenant)
        self._history_repo = ViewingStatusHistoryRepository(session, tenant)
        self._listing_repo = ListingRepository(session, tenant)

    async def book_viewing(self, listing_id: UUID, user_id: UUID, data: dict) -> ScheduledViewing:
        listing = await self._listing_repo.get_by_id(listing_id)
        if listing is None or listing.status != "active":
            raise NotFoundError(detail="Listing not found or not active")

        slot_id = data["viewing_slot_id"]
        slot = await self._slot_repo.get_by_id(slot_id)
        if slot is None or slot.status != "active":
            raise NotFoundError(detail="Viewing slot not available")
        if str(slot.listing_id) != str(listing_id):
            raise NotFoundError(detail="Viewing slot not found for this listing")

        if slot.reserved_count >= slot.capacity:
            raise ConflictError(detail="Viewing slot is fully booked")

        # Public users can read active listings/slots, but booking mutates tenant-owned rows.
        # Switch this transaction into the listing tenant context before reserve/create writes.
        await apply_rls_context_to_session(
            self._session,
            tenant_id=listing.agency_tenant_id,
            user_id=user_id,
            role="user",
            is_platform_admin=False,
        )

        slot = await self._slot_repo.increment_reserved_count(slot_id)
        if slot is None or slot.reserved_count > slot.capacity:
            raise ConflictError(detail="Viewing slot became unavailable")

        viewing = ScheduledViewing(
            agency_tenant_id=listing.agency_tenant_id,
            listing_id=listing_id,
            viewing_slot_id=slot_id,
            user_id=user_id,
            status="scheduled",
            scheduled_start_at=slot.starts_at,
            scheduled_end_at=slot.ends_at,
            notes=data.get("notes"),
        )
        viewing = await self._viewing_repo.create(viewing)

        history = ScheduledViewingStatusHistory(
            scheduled_viewing_id=viewing.id,
            agency_tenant_id=listing.agency_tenant_id,
            old_status=None,
            new_status="scheduled",
            changed_by_user_id=user_id,
            reason="Booking created",
        )
        await self._history_repo.create(history)

        await write_domain_event_log(
            self._session, "viewing.scheduled",
            aggregate_type="viewing", aggregate_id=str(viewing.id),
            agency_tenant_id=listing.agency_tenant_id, actor_user_id=user_id,
            payload={"listing_id": str(listing_id), "slot_id": str(slot_id)},
        )

        return viewing

    async def list_user_viewings(self, user_id: UUID, pagination: PaginationRequest) -> PaginationResult:
        items, total = await self._viewing_repo.list_by_user(
            user_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def get_user_viewing(self, viewing_id: UUID, user_id: UUID) -> ScheduledViewing:
        viewing = await self._viewing_repo.get_by_id(viewing_id)
        if viewing is None:
            raise NotFoundError(detail="Scheduled viewing not found")
        if str(viewing.user_id) != str(user_id):
            raise ForbiddenError(detail="Not your scheduled viewing")
        return viewing

    async def list_tenant_viewings(
        self, pagination: PaginationRequest,
        status: Optional[str] = None,
        listing_id: Optional[UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._viewing_repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit,
            status=status, listing_id=listing_id, date_from=date_from, date_to=date_to,
        )
        serialized_items = await self._attach_listing_summaries(items)
        return PaginationResult(items=serialized_items, total=total, pagination=pagination)

    async def _attach_listing_summaries(self, items: list[ScheduledViewing]) -> list[dict]:
        if not items:
            return []

        listing_ids = list({item.listing_id for item in items})
        result = await self._session.execute(
            select(Listing).where(Listing.id.in_(listing_ids))
        )
        listing_map = {listing.id: listing for listing in result.scalars().all()}
        thumbnail_map = await build_thumbnail_map(self._session, listing_ids)

        serialized: list[dict] = []
        for item in items:
            payload = {
                "id": item.id,
                "agency_tenant_id": item.agency_tenant_id,
                "listing_id": item.listing_id,
                "viewing_slot_id": item.viewing_slot_id,
                "user_id": item.user_id,
                "status": item.status,
                "scheduled_start_at": item.scheduled_start_at,
                "scheduled_end_at": item.scheduled_end_at,
                "notes": item.notes,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "listing_summary": None,
            }
            listing = listing_map.get(item.listing_id)
            if listing is not None:
                payload["listing_summary"] = {
                    "id": listing.id,
                    "title": listing.title,
                    "thumbnail_url": thumbnail_map.get(listing.id),
                }
            serialized.append(payload)
        return serialized

    async def get_tenant_viewing(self, viewing_id: UUID) -> ScheduledViewing:
        ctx = require_tenant(self._tenant)
        viewing = await self._viewing_repo.get_by_id(viewing_id)
        if viewing is None:
            raise NotFoundError(detail="Scheduled viewing not found")
        ensure_tenant_match(self._tenant, viewing.agency_tenant_id)
        enriched = await self._attach_listing_summaries([viewing])
        return enriched[0]

    async def update_viewing_status(self, viewing_id: UUID, new_status: str, reason: Optional[str] = None) -> ScheduledViewing:
        from app.common.domain import VIEWING_STATUS_TRANSITIONS, VALID_VIEWING_STATUSES

        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot modify viewing schedules")

        viewing = await self._viewing_repo.get_by_id(viewing_id)
        if viewing is None:
            raise NotFoundError(detail="Scheduled viewing not found")
        ensure_tenant_match(self._tenant, viewing.agency_tenant_id)

        if new_status not in VALID_VIEWING_STATUSES:
            raise ValidationError(detail=f"Invalid viewing status: {new_status}")
        allowed = VIEWING_STATUS_TRANSITIONS.get(viewing.status, [])
        if new_status not in allowed:
            raise ValidationError(
                detail=f"Cannot transition from '{viewing.status}' to '{new_status}'"
            )

        old_status = viewing.status
        viewing.status = new_status
        await self._session.flush()

        history = ScheduledViewingStatusHistory(
            scheduled_viewing_id=viewing.id,
            agency_tenant_id=viewing.agency_tenant_id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=ctx.actor_id,
            reason=reason,
        )
        await self._history_repo.create(history)

        await write_domain_event_log(
            self._session, "viewing.status_changed",
            aggregate_type="viewing", aggregate_id=str(viewing.id),
            agency_tenant_id=viewing.agency_tenant_id, actor_user_id=ctx.actor_id,
            payload={"old_status": old_status, "new_status": new_status},
        )

        return viewing
