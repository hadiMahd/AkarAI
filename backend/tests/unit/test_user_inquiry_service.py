import pytest
import uuid
from datetime import datetime, timezone

from app.leads.models import Lead
from app.leads.repository import LeadRepository
from app.common.domain import LEAD_STATUS_NEW


@pytest.mark.anyio
class TestLeadRepository:
    async def test_create_lead(self, db_session, test_tenant, test_user, test_listing):
        user, _ = test_user
        repo = LeadRepository(db_session)
        
        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test Lead",
            email="test@example.com",
            phone="+1234567890",
            message="I'm interested in this property",
            source="web",
        )
        result = await repo.create(lead)
        
        assert result.id is not None
        assert result.agency_tenant_id == test_tenant.id
        assert result.listing_id == test_listing.id
        assert result.user_id == user.id
        assert result.status == LEAD_STATUS_NEW
        assert result.name == "Test Lead"
        assert result.email == "test@example.com"

    async def test_get_by_id(self, db_session, test_tenant, test_user, test_listing):
        user, _ = test_user
        repo = LeadRepository(db_session)
        
        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test Lead",
            email="test@example.com",
        )
        await repo.create(lead)
        
        result = await repo.get_by_id(lead.id)
        assert result is not None
        assert result.id == lead.id
        assert result.user_id == user.id

    async def test_get_by_id_not_found(self, db_session):
        repo = LeadRepository(db_session)
        
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_list_by_tenant(self, db_session, test_tenant, test_user, test_listing):
        user, _ = test_user
        repo = LeadRepository(db_session)
        
        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test Lead",
            email="test@example.com",
        )
        await repo.create(lead)
        
        items, total = await repo.list_by_tenant(test_tenant.id, offset=0, limit=10)
        assert total >= 1
        assert len(items) >= 1
        assert items[0].agency_tenant_id == test_tenant.id

    async def test_lead_source_tracking(self, db_session, test_tenant, test_user, test_listing):
        user, _ = test_user
        repo = LeadRepository(db_session)
        
        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            name="Test Lead",
            email="test@example.com",
            source="web",
        )
        result = await repo.create(lead)
        
        assert result.source == "web"

    async def test_lead_optional_fields(self, db_session, test_tenant, test_user, test_listing):
        user, _ = test_user
        repo = LeadRepository(db_session)
        
        lead = Lead(
            agency_tenant_id=test_tenant.id,
            listing_id=test_listing.id,
            user_id=user.id,
            status=LEAD_STATUS_NEW,
            message="Optional message",
        )
        result = await repo.create(lead)
        
        assert result.name is None
        assert result.email is None
        assert result.phone is None
        assert result.message == "Optional message"
