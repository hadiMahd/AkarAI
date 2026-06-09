import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.common.domain import (
    VIEWING_STATUS_SCHEDULED,
    VIEWING_STATUS_CANCELLED_BY_USER,
    VIEWING_STATUS_CANCELLED_BY_AGENCY,
    VIEWING_STATUS_COMPLETED,
    VIEWING_STATUS_NO_SHOW,
)
from app.common.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.common.pagination import PaginationRequest
from app.common.tenant import TenantContext
from app.viewings.models import ListingViewingSlot, ScheduledViewing, ScheduledViewingStatusHistory
from app.viewings.service import ViewingBookingService


def _make_tenant(tenant_id, actor_id, role="agency_admin"):
    return TenantContext(
        actor_id=actor_id,
        role=role,
        permissions=[],
        tenant_id=tenant_id,
    )


async def _create_slot(db_session, tenant_id, listing_id, user_id):
    slot = ListingViewingSlot(
        listing_id=listing_id,
        agency_tenant_id=tenant_id,
        starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
        capacity=5,
        reserved_count=0,
        status="active",
        created_by_user_id=user_id,
    )
    db_session.add(slot)
    await db_session.flush()
    return slot


async def _create_viewing(db_session, tenant_id, listing_id, slot_id, user_id, status=VIEWING_STATUS_SCHEDULED):
    viewing = ScheduledViewing(
        agency_tenant_id=tenant_id,
        listing_id=listing_id,
        viewing_slot_id=slot_id,
        user_id=user_id,
        status=status,
        scheduled_start_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scheduled_end_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db_session.add(viewing)
    await db_session.commit()
    return viewing


@pytest.mark.anyio
class TestViewingStatusTransitions:
    async def test_scheduled_to_completed(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        updated = await svc.update_viewing_status(viewing.id, VIEWING_STATUS_COMPLETED)
        assert updated.status == VIEWING_STATUS_COMPLETED

    async def test_scheduled_to_cancelled_by_user(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        updated = await svc.update_viewing_status(viewing.id, VIEWING_STATUS_CANCELLED_BY_USER)
        assert updated.status == VIEWING_STATUS_CANCELLED_BY_USER

    async def test_scheduled_to_cancelled_by_agency(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        updated = await svc.update_viewing_status(viewing.id, VIEWING_STATUS_CANCELLED_BY_AGENCY, reason="Agent unavailable")
        assert updated.status == VIEWING_STATUS_CANCELLED_BY_AGENCY

    async def test_scheduled_to_no_show(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        updated = await svc.update_viewing_status(viewing.id, VIEWING_STATUS_NO_SHOW)
        assert updated.status == VIEWING_STATUS_NO_SHOW

    async def test_terminal_status_cannot_transition(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id, status=VIEWING_STATUS_COMPLETED)

        svc = ViewingBookingService(db_session, ctx)
        with pytest.raises(ValidationError, match="Cannot transition"):
            await svc.update_viewing_status(viewing.id, VIEWING_STATUS_SCHEDULED)

    async def test_invalid_status_value_rejected(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        with pytest.raises(ValidationError, match="Invalid viewing status"):
            await svc.update_viewing_status(viewing.id, "nonexistent")

    async def test_status_update_creates_history_record(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        await svc.update_viewing_status(viewing.id, VIEWING_STATUS_COMPLETED, reason="Done")

        from sqlalchemy import select
        result = await db_session.execute(
            select(ScheduledViewingStatusHistory).where(
                ScheduledViewingStatusHistory.scheduled_viewing_id == viewing.id
            )
        )
        history_records = result.scalars().all()
        assert len(history_records) >= 1
        last = history_records[-1]
        assert last.old_status == VIEWING_STATUS_SCHEDULED
        assert last.new_status == VIEWING_STATUS_COMPLETED
        assert last.reason == "Done"

    async def test_status_update_viewing_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Scheduled viewing not found"):
            await svc.update_viewing_status(uuid.uuid4(), VIEWING_STATUS_COMPLETED)

    async def test_status_update_without_tenant_raises(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, None)
        with pytest.raises(PermissionError):
            await svc.update_viewing_status(viewing.id, VIEWING_STATUS_COMPLETED)


@pytest.mark.anyio
class TestViewingBookingServiceListAndGet:
    async def test_list_user_viewings(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user

        for _ in range(3):
            slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
            await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session)
        result = await svc.list_user_viewings(user.id, PaginationRequest(page=1, page_size=10))
        assert result.total >= 3

    async def test_get_user_viewing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session)
        fetched = await svc.get_user_viewing(viewing.id, user.id)
        assert fetched.id == viewing.id

    async def test_get_user_viewing_wrong_user(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_user_id = uuid.uuid4()
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        viewing = await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session)
        with pytest.raises(ForbiddenError, match="Not your scheduled viewing"):
            await svc.get_user_viewing(viewing.id, other_user_id)

    async def test_list_tenant_viewings(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)
        await _create_viewing(db_session, test_tenant.id, test_listing.id, slot.id, user.id)

        svc = ViewingBookingService(db_session, ctx)
        result = await svc.list_tenant_viewings(PaginationRequest(page=1, page_size=10))
        assert result.total >= 1
