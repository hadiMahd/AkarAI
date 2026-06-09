import uuid
from datetime import datetime, timezone

import pytest

from app.common.domain import LEAD_STATUS_NEW, LEAD_STATUS_REVIEWED, LEAD_STATUS_CLOSED
from app.common.exceptions import NotFoundError, ValidationError
from app.common.pagination import PaginationRequest
from app.common.tenant import TenantContext
from app.leads.models import Lead
from app.leads.service import LeadService


def _make_tenant(tenant_id, actor_id, role="agency_admin"):
    return TenantContext(
        actor_id=actor_id,
        role=role,
        permissions=[],
        tenant_id=tenant_id,
    )


@pytest.mark.anyio
class TestLeadServiceStatusTransitions:
    async def test_update_status_new_to_reviewed(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        updated = await svc.update_lead_status(lead.id, LEAD_STATUS_REVIEWED)
        assert updated.status == LEAD_STATUS_REVIEWED

    async def test_update_status_new_to_closed(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        updated = await svc.update_lead_status(lead.id, LEAD_STATUS_CLOSED)
        assert updated.status == LEAD_STATUS_CLOSED
        assert updated.closed_at is not None

    async def test_update_status_reviewed_to_closed(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_REVIEWED,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        updated = await svc.update_lead_status(lead.id, LEAD_STATUS_CLOSED)
        assert updated.status == LEAD_STATUS_CLOSED

    async def test_update_status_invalid_transition_closed_to_new(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_CLOSED,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        with pytest.raises(ValidationError, match="Cannot transition"):
            await svc.update_lead_status(lead.id, LEAD_STATUS_NEW)

    async def test_update_status_invalid_status_value(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        with pytest.raises(ValidationError, match="Invalid lead status"):
            await svc.update_lead_status(lead.id, "nonexistent")

    async def test_update_status_lead_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = LeadService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Lead not found"):
            await svc.update_lead_status(uuid.uuid4(), LEAD_STATUS_REVIEWED)

    async def test_update_status_without_tenant_raises(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, None)
        with pytest.raises(PermissionError):
            await svc.update_lead_status(lead.id, LEAD_STATUS_REVIEWED)


@pytest.mark.anyio
class TestLeadServiceReview:
    async def test_review_lead_transitions_status(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        record = await svc.review_lead(lead.id, user.id, {"outcome": "interested", "notes": "Good lead"})
        assert record.outcome == "interested"
        assert record.notes == "Good lead"
        assert record.lead_id == lead.id

        await db_session.refresh(lead)
        assert lead.status == LEAD_STATUS_REVIEWED

    async def test_review_already_reviewed_lead(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_REVIEWED,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        record = await svc.review_lead(lead.id, user.id, {"outcome": "not_interested"})
        assert record.outcome == "not_interested"

        await db_session.refresh(lead)
        assert lead.status == LEAD_STATUS_REVIEWED

    async def test_review_lead_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = LeadService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Lead not found"):
            await svc.review_lead(uuid.uuid4(), user.id, {"outcome": "test"})


@pytest.mark.anyio
class TestLeadServiceListAndGet:
    async def test_list_tenant_leads(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        for i in range(3):
            lead = Lead(
                agency_tenant_id=test_tenant.id,
                listing_id=test_listing.id,
                user_id=user.id,
                status=LEAD_STATUS_NEW,
                name=f"Lead {i}",
                email=f"lead{i}@test.com",
            )
            db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        result = await svc.list_tenant_leads(PaginationRequest(page=1, page_size=10))
        assert result.total >= 3
        assert len(result.items) >= 3

    async def test_get_lead(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test",
            email="test@test.com",
        )
        db_session.add(lead)
        await db_session.commit()

        svc = LeadService(db_session, ctx)
        fetched = await svc.get_lead(lead.id)
        assert fetched.id == lead.id
        assert fetched.name == "Test"

    async def test_get_lead_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = LeadService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Lead not found"):
            await svc.get_lead(uuid.uuid4())
