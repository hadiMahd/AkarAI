import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.agencies.models import AgencyProfile, AgencyEmployeeMembership
from app.agencies.service import AgencyService
from app.common.tenant import TenantContext
from app.listings.models import Listing, ListingPhotoMetadata
from app.listings.service import ListingService
from app.viewings.models import ListingViewingSlot
from app.viewings.service import ViewingSlotService
from app.common.pagination import PaginationRequest


def _make_tenant(tenant_id, actor_id, role="agency_admin"):
    return TenantContext(
        actor_id=actor_id,
        role=role,
        permissions=[],
        tenant_id=tenant_id,
    )


@pytest.mark.anyio
class TestAgencyProfileTenantIsolation:
    async def test_get_profile_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        profile = AgencyProfile(
            agency_tenant_id=test_tenant.id,
            display_name="Test Agency",
        )
        db_session.add(profile)
        await db_session.commit()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = AgencyService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        with pytest.raises(NotFoundError, match="Agency profile not found"):
            await svc.get_profile()

    async def test_update_profile_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        profile = AgencyProfile(
            agency_tenant_id=test_tenant.id,
            display_name="Test Agency",
        )
        db_session.add(profile)
        await db_session.commit()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = AgencyService(db_session, other_ctx)
        from sqlalchemy.exc import IntegrityError
        from app.common.exceptions import NotFoundError
        with pytest.raises((NotFoundError, IntegrityError)):
            await svc.update_profile({"display_name": "Should Fail"})

    async def test_list_employees_only_own_tenant(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1"))
        role_id = result.fetchone()[0]

        membership = AgencyEmployeeMembership(
            agency_tenant_id=test_tenant.id,
            user_id=user.id,
            role_id=role_id,
            status="active",
        )
        db_session.add(membership)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        result = await svc.list_employees(PaginationRequest(page=1, page_size=100))
        for item in result.items:
            assert str(item.agency_tenant_id) == str(test_tenant.id)


@pytest.mark.anyio
class TestListingTenantIsolation:
    async def test_get_listing_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = ListingService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        with pytest.raises((NotFoundError, PermissionError)):
            await svc.get_listing(test_listing.id)

    async def test_update_listing_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = ListingService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        with pytest.raises((NotFoundError, PermissionError)):
            await svc.update_listing(test_listing.id, {"title": "Should Fail"})

    async def test_archive_listing_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = ListingService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        with pytest.raises((NotFoundError, PermissionError)):
            await svc.archive_listing(test_listing.id)

    async def test_list_listings_only_own_tenant(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = ListingService(db_session, ctx)
        result = await svc.list_tenant_listings(PaginationRequest(page=1, page_size=100))
        for item in result.items:
            assert str(item.agency_tenant_id) == str(test_tenant.id)


@pytest.mark.anyio
class TestPhotoMetadataTenantIsolation:
    async def test_create_photo_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = ListingService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        with pytest.raises((NotFoundError, PermissionError)):
            await svc.create_photo(test_listing.id, {"object_key": "test/photo.jpg"})

    async def test_list_photos_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = ListingService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        with pytest.raises((NotFoundError, PermissionError)):
            await svc.list_photos(test_listing.id)


@pytest.mark.anyio
class TestViewingSlotTenantIsolation:
    async def test_list_slots_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        slot = ListingViewingSlot(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            capacity=5,
            reserved_count=0,
            status="active",
            created_by_user_id=user.id,
        )
        db_session.add(slot)
        await db_session.commit()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = ViewingSlotService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        with pytest.raises((NotFoundError, PermissionError)):
            await svc.list_slots(test_listing.id)

    async def test_create_slot_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        other_ctx = _make_tenant(other_tenant_id, user.id)
        svc = ViewingSlotService(db_session, other_ctx)
        from app.common.exceptions import NotFoundError
        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)
        with pytest.raises((NotFoundError, PermissionError)):
            await svc.create_slot(test_listing.id, {
                "starts_at": starts,
                "ends_at": ends,
                "capacity": 5,
            })


@pytest.mark.anyio
class TestAgencyCoreAPITenantIsolation:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_agency_profile_requires_tenant_membership(self, async_client: AsyncClient):
        token = await self._login(async_client, "user@akarai.test")
        with pytest.raises(PermissionError):
            await async_client.get("/agencies/me/profile", headers={"Authorization": f"Bearer {token}"})

    async def test_agency_employees_requires_tenant_membership(self, async_client: AsyncClient):
        token = await self._login(async_client, "user@akarai.test")
        with pytest.raises(PermissionError):
            await async_client.get("/agencies/me/employees", headers={"Authorization": f"Bearer {token}"})

    async def test_agency_listings_requires_tenant_membership(self, async_client: AsyncClient):
        token = await self._login(async_client, "user@akarai.test")
        with pytest.raises(PermissionError):
            await async_client.get("/agency/listings", headers={"Authorization": f"Bearer {token}"})
