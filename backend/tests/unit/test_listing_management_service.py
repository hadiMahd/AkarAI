import uuid
from datetime import datetime, timezone

import pytest

from app.common.domain import (
    LISTING_STATUS_ACTIVE,
    LISTING_STATUS_INACTIVE,
    LISTING_STATUS_ARCHIVED,
)
from app.common.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.common.pagination import PaginationRequest
from app.common.tenant import TenantContext
from app.listings.models import Listing, ListingPhotoMetadata
from app.listings.service import ListingService


def _make_tenant(tenant_id, actor_id, role="agency_admin"):
    return TenantContext(
        actor_id=actor_id,
        role=role,
        permissions=[],
        tenant_id=tenant_id,
    )


@pytest.mark.anyio
class TestListingServiceStatusValidation:
    async def test_create_listing_default_status(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        listing = await svc.create_listing({
            "title": "Test Listing",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
        })
        assert listing.status == "inactive"

    async def test_create_listing_with_status(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        listing = await svc.create_listing({
            "title": "Active Listing",
            "property_type": "villa",
            "listing_purpose": "rent",
            "price": 5000,
            "status": "active",
        })
        assert listing.status == "active"

    async def test_create_listing_invalid_status(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        with pytest.raises(ValidationError, match="Invalid listing status"):
            await svc.create_listing({
                "title": "Bad Status",
                "status": "invalid_status",
            })

    async def test_update_listing_status_inactive_to_active(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        test_listing.status = LISTING_STATUS_INACTIVE
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        updated = await svc.update_listing(test_listing.id, {"status": LISTING_STATUS_ACTIVE})
        assert updated.status == LISTING_STATUS_ACTIVE

    async def test_update_listing_status_active_to_archived(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        test_listing.status = LISTING_STATUS_ACTIVE
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        updated = await svc.update_listing(test_listing.id, {"status": LISTING_STATUS_ARCHIVED})
        assert updated.status == LISTING_STATUS_ARCHIVED
        assert updated.archived_at is not None

    async def test_update_listing_status_archived_is_terminal(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        test_listing.status = LISTING_STATUS_ARCHIVED
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        with pytest.raises(ValidationError, match="Cannot transition"):
            await svc.update_listing(test_listing.id, {"status": LISTING_STATUS_ACTIVE})

    async def test_update_listing_invalid_status(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        with pytest.raises(ValidationError, match="Invalid listing status"):
            await svc.update_listing(test_listing.id, {"status": "nonexistent"})

    async def test_archive_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        test_listing.status = LISTING_STATUS_ACTIVE
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        await svc.archive_listing(test_listing.id)
        await db_session.refresh(test_listing)
        assert test_listing.status == LISTING_STATUS_ARCHIVED
        assert test_listing.archived_at is not None

    async def test_archive_already_archived_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        test_listing.status = LISTING_STATUS_ARCHIVED
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        await svc.archive_listing(test_listing.id)
        await db_session.refresh(test_listing)
        assert test_listing.status == LISTING_STATUS_ARCHIVED


@pytest.mark.anyio
class TestListingServiceSupportEmployeeRestrictions:
    async def test_create_listing_support_employee_forbidden(self, db_session, test_tenant, support_user):
        user, _ = support_user
        ctx = _make_tenant(test_tenant.id, user.id, role="support_employee")

        svc = ListingService(db_session, ctx)
        with pytest.raises(ForbiddenError, match="Support employees cannot create listings"):
            await svc.create_listing({
                "title": "Should Fail",
                "property_type": "apartment",
            })


@pytest.mark.anyio
class TestListingServicePhotoMetadata:
    async def test_list_photos(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/photo.jpg",
            display_order=1,
            status="active",
        )
        db_session.add(photo)
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        photos = await svc.list_photos(test_listing.id)
        assert len(photos) >= 1

    async def test_create_photo(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        photo = await svc.create_photo(test_listing.id, {
            "object_key": "test/new_photo.jpg",
            "caption": "New photo",
        })
        assert photo.object_key == "test/new_photo.jpg"
        assert photo.display_order == 1

    async def test_create_photo_listing_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Listing not found"):
            await svc.create_photo(uuid.uuid4(), {"object_key": "test/photo.jpg"})

    async def test_update_photo(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/photo.jpg",
            display_order=1,
            status="active",
        )
        db_session.add(photo)
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        updated = await svc.update_photo(test_listing.id, photo.id, {
            "caption": "Updated caption",
            "alt_text": "Updated alt text",
        })
        assert updated.caption == "Updated caption"
        assert updated.alt_text == "Updated alt text"

    async def test_remove_photo(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/photo.jpg",
            display_order=1,
            status="active",
        )
        db_session.add(photo)
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        await svc.remove_photo(test_listing.id, photo.id)
        await db_session.refresh(photo)
        assert photo.status == "removed"


@pytest.mark.anyio
class TestListingServiceListAndGet:
    async def test_list_tenant_listings(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        result = await svc.list_tenant_listings(PaginationRequest(page=1, page_size=10))
        assert result.total >= 1

    async def test_get_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        fetched = await svc.get_listing(test_listing.id)
        assert fetched.id == test_listing.id

    async def test_get_listing_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Listing not found"):
            await svc.get_listing(uuid.uuid4())
