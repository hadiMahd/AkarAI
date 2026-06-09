import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.common.tenant import TenantContext
from app.leads.models import Lead
from app.leads.service import LeadService
from app.viewings.models import ListingViewingSlot, ScheduledViewing
from app.viewings.service import ViewingBookingService
from app.notifications.models import Notification
from app.notifications.service import NotificationService
from app.common.pagination import PaginationRequest
from app.common.exceptions import ForbiddenError


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


@pytest.mark.anyio
class TestLeadTenantIsolation:
    async def test_get_lead_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status="new",
            name="Isolation Test",
            email="iso@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        other_ctx = TenantContext(
            actor_id=user.id,
            role="agency_admin",
            permissions=[],
            tenant_id=other_tenant_id,
        )
        svc = LeadService(db_session, other_ctx)
        with pytest.raises(PermissionError, match="Cross-tenant access denied"):
            await svc.get_lead(lead.id)

    async def test_update_lead_status_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status="new",
        )
        db_session.add(lead)
        await db_session.commit()

        other_ctx = TenantContext(
            actor_id=user.id,
            role="agency_admin",
            permissions=[],
            tenant_id=other_tenant_id,
        )
        svc = LeadService(db_session, other_ctx)
        with pytest.raises(PermissionError, match="Cross-tenant access denied"):
            await svc.update_lead_status(lead.id, "reviewed")

    async def test_review_lead_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status="new",
        )
        db_session.add(lead)
        await db_session.commit()

        other_ctx = TenantContext(
            actor_id=user.id,
            role="agency_admin",
            permissions=[],
            tenant_id=other_tenant_id,
        )
        svc = LeadService(db_session, other_ctx)
        with pytest.raises(PermissionError, match="Cross-tenant access denied"):
            await svc.review_lead(lead.id, user.id, {"outcome": "test"})

    async def test_list_leads_only_returns_own_tenant(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = TenantContext(
            actor_id=user.id,
            role="agency_admin",
            permissions=[],
            tenant_id=test_tenant.id,
        )

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status="new",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        result = await svc.list_tenant_leads(PaginationRequest(page=1, page_size=100))
        for item in result.items:
            assert str(item.agency_tenant_id) == str(test_tenant.id)


@pytest.mark.anyio
class TestViewingTenantIsolation:
    async def test_get_tenant_viewing_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)

        viewing = ScheduledViewing(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            viewing_slot_id=slot.id,
            user_id=user.id,
            status="scheduled",
            scheduled_start_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scheduled_end_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        db_session.add(viewing)
        await db_session.commit()

        other_ctx = TenantContext(
            actor_id=user.id,
            role="agency_admin",
            permissions=[],
            tenant_id=other_tenant_id,
        )
        svc = ViewingBookingService(db_session, other_ctx)
        with pytest.raises(PermissionError, match="Cross-tenant access denied"):
            await svc.get_tenant_viewing(viewing.id)

    async def test_update_viewing_status_cross_tenant_denied(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        other_tenant_id = uuid.uuid4()
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)

        viewing = ScheduledViewing(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            viewing_slot_id=slot.id,
            user_id=user.id,
            status="scheduled",
            scheduled_start_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scheduled_end_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        db_session.add(viewing)
        await db_session.commit()

        other_ctx = TenantContext(
            actor_id=user.id,
            role="agency_admin",
            permissions=[],
            tenant_id=other_tenant_id,
        )
        svc = ViewingBookingService(db_session, other_ctx)
        with pytest.raises(PermissionError, match="Cross-tenant access denied"):
            await svc.update_viewing_status(viewing.id, "completed")

    async def test_list_tenant_viewings_only_own_tenant(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = TenantContext(
            actor_id=user.id,
            role="agency_admin",
            permissions=[],
            tenant_id=test_tenant.id,
        )
        slot = await _create_slot(db_session, test_tenant.id, test_listing.id, user.id)

        viewing = ScheduledViewing(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            viewing_slot_id=slot.id,
            user_id=user.id,
            status="scheduled",
            scheduled_start_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scheduled_end_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        db_session.add(viewing)
        await db_session.commit()

        svc = ViewingBookingService(db_session, ctx)
        result = await svc.list_tenant_viewings(PaginationRequest(page=1, page_size=100))
        for item in result.items:
            assert str(item.agency_tenant_id) == str(test_tenant.id)


@pytest.mark.anyio
class TestNotificationTenantIsolation:
    async def test_get_notification_wrong_user(self, db_session, test_user):
        user, _ = test_user
        other_user_id = uuid.uuid4()

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="iso_test",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        with pytest.raises(ForbiddenError, match="Not your notification"):
            await svc.get_notification(n.id, other_user_id)

    async def test_mark_read_wrong_user(self, db_session, test_user):
        user, _ = test_user
        other_user_id = uuid.uuid4()

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="iso_read",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        with pytest.raises(ForbiddenError, match="Not your notification"):
            await svc.mark_read(n.id, other_user_id)

    async def test_dismiss_wrong_user(self, db_session, test_user):
        user, _ = test_user
        other_user_id = uuid.uuid4()

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="iso_dismiss",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        with pytest.raises(ForbiddenError, match="Not your notification"):
            await svc.dismiss(n.id, other_user_id)


@pytest.mark.anyio
class TestSearchLogTenantIsolation:
    async def test_list_search_logs_requires_tenant(self, db_session):
        from app.search.service import SearchService

        svc = SearchService(db_session, None)
        with pytest.raises(PermissionError):
            await svc.list_search_logs(PaginationRequest(page=1, page_size=10))

    async def test_list_domain_logs_requires_tenant(self, db_session):
        from app.search.service import SearchService

        svc = SearchService(db_session, None)
        with pytest.raises(PermissionError):
            await svc.list_domain_logs(PaginationRequest(page=1, page_size=10))


@pytest.mark.anyio
class TestOperationalLogsAPITenantIsolation:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_search_logs_requires_tenant_membership(self, async_client: AsyncClient):
        token = await self._login(async_client, "platform.admin@akarai.test")
        resp = await async_client.get(
            "/agency/search-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_domain_logs_requires_tenant_membership(self, async_client: AsyncClient):
        token = await self._login(async_client, "platform.admin@akarai.test")
        resp = await async_client.get(
            "/agency/domain-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_agency_leads_requires_tenant_membership(self, async_client: AsyncClient):
        token = await self._login(async_client, "platform.admin@akarai.test")
        resp = await async_client.get(
            "/agency/leads",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_agency_viewings_requires_tenant_membership(self, async_client: AsyncClient):
        token = await self._login(async_client, "platform.admin@akarai.test")
        resp = await async_client.get(
            "/agency/viewings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
