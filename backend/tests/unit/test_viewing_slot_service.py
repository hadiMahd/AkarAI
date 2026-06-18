import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.common.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.common.tenant import TenantContext
from app.viewings.models import ListingViewingSlot
from app.viewings.service import ViewingSlotService


def _make_tenant(tenant_id, actor_id, role="agency_admin"):
    return TenantContext(
        actor_id=actor_id,
        role=role,
        permissions=[],
        tenant_id=tenant_id,
    )


@pytest.mark.anyio
class TestViewingSlotServiceValidation:
    async def test_list_slots(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        slot = ListingViewingSlot(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            capacity=3,
            reserved_count=0,
            status="active",
            created_by_user_id=user.id,
        )
        db_session.add(slot)
        await db_session.commit()

        svc = ViewingSlotService(db_session, ctx)
        slots = await svc.list_slots(test_listing.id)
        assert len(slots) >= 1

    async def test_list_slots_listing_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Listing not found"):
            await svc.list_slots(uuid.uuid4())

    async def test_create_slot(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)

        svc = ViewingSlotService(db_session, ctx)
        slot = await svc.create_slot(test_listing.id, {
            "starts_at": starts,
            "ends_at": ends,
            "capacity": 5,
        })
        assert slot.capacity == 5
        assert slot.reserved_count == 0
        assert slot.status == "active"

    async def test_create_slot_invalid_time_range(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts - timedelta(hours=1)

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(ValidationError, match="ends_at must be after starts_at"):
            await svc.create_slot(test_listing.id, {
                "starts_at": starts,
                "ends_at": ends,
                "capacity": 5,
            })

    async def test_create_slot_equal_time_range(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(ValidationError, match="ends_at must be after starts_at"):
            await svc.create_slot(test_listing.id, {
                "starts_at": starts,
                "ends_at": ends,
                "capacity": 5,
            })

    async def test_create_slot_requires_future_start_time(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        starts = datetime.now(timezone.utc) + timedelta(minutes=2)
        ends = starts + timedelta(hours=1)

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(ValidationError, match="at least 5 minutes in the future"):
            await svc.create_slot(test_listing.id, {
                "starts_at": starts,
                "ends_at": ends,
                "capacity": 5,
            })

    async def test_create_slot_support_employee_forbidden(self, db_session, test_tenant, support_user, test_listing):
        user, _ = support_user
        ctx = _make_tenant(test_tenant.id, user.id, role="support_employee")

        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(ForbiddenError, match="Support employees cannot create viewing slots"):
            await svc.create_slot(test_listing.id, {
                "starts_at": starts,
                "ends_at": ends,
                "capacity": 5,
            })

    async def test_create_slot_listing_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Listing not found"):
            await svc.create_slot(uuid.uuid4(), {
                "starts_at": starts,
                "ends_at": ends,
                "capacity": 5,
            })

    async def test_update_slot(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        slot = ListingViewingSlot(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            capacity=3,
            reserved_count=0,
            status="active",
            created_by_user_id=user.id,
        )
        db_session.add(slot)
        await db_session.commit()

        svc = ViewingSlotService(db_session, ctx)
        updated = await svc.update_slot(test_listing.id, slot.id, {
            "capacity": 10,
        })
        assert updated.capacity == 10

    async def test_update_slot_invalid_time_range(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        slot = ListingViewingSlot(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            capacity=3,
            reserved_count=0,
            status="active",
            created_by_user_id=user.id,
        )
        db_session.add(slot)
        await db_session.commit()

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(ValidationError, match="ends_at must be after starts_at"):
            await svc.update_slot(test_listing.id, slot.id, {
                "starts_at": datetime.now(timezone.utc) + timedelta(hours=5),
                "ends_at": datetime.now(timezone.utc) + timedelta(hours=3),
            })

    async def test_update_slot_requires_future_start_time(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        slot = ListingViewingSlot(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            capacity=3,
            reserved_count=0,
            status="active",
            created_by_user_id=user.id,
        )
        db_session.add(slot)
        await db_session.commit()

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(ValidationError, match="at least 5 minutes in the future"):
            await svc.update_slot(test_listing.id, slot.id, {
                "starts_at": datetime.now(timezone.utc) + timedelta(minutes=2),
            })

    async def test_update_slot_not_found(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Viewing slot not found"):
            await svc.update_slot(test_listing.id, uuid.uuid4(), {"capacity": 10})

    async def test_update_slot_wrong_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        slot = ListingViewingSlot(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            capacity=3,
            reserved_count=0,
            status="active",
            created_by_user_id=user.id,
        )
        db_session.add(slot)
        await db_session.commit()

        other_listing_id = uuid.uuid4()
        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Slot not found for this listing"):
            await svc.update_slot(other_listing_id, slot.id, {"capacity": 10})

    async def test_deactivate_slot(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        slot = ListingViewingSlot(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            capacity=3,
            reserved_count=0,
            status="active",
            created_by_user_id=user.id,
        )
        db_session.add(slot)
        await db_session.commit()

        svc = ViewingSlotService(db_session, ctx)
        await svc.deactivate_slot(test_listing.id, slot.id)
        await db_session.refresh(slot)
        assert slot.status == "inactive"

    async def test_deactivate_slot_not_found(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ViewingSlotService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Viewing slot not found"):
            await svc.deactivate_slot(test_listing.id, uuid.uuid4())

    async def test_create_slot_without_tenant_raises(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user

        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)

        svc = ViewingSlotService(db_session, None)
        with pytest.raises(PermissionError):
            await svc.create_slot(test_listing.id, {
                "starts_at": starts,
                "ends_at": ends,
                "capacity": 5,
            })
