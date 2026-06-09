import pytest
import uuid
from datetime import datetime, timezone

from app.listings.models import SavedListing, Listing
from app.listings.repository import SavedListingRepository


@pytest.mark.anyio
class TestSavedListingRepository:
    async def test_create_saved_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        result = await repo.create(saved)
        
        assert result.id is not None
        assert result.user_id == user.id
        assert result.listing_id == test_listing.id
        assert result.deleted_at is None

    async def test_get_by_user_and_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved)
        
        result = await repo.get_by_user_and_listing(user.id, test_listing.id)
        assert result is not None
        assert result.user_id == user.id
        assert result.listing_id == test_listing.id

    async def test_get_by_user_and_listing_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        result = await repo.get_by_user_and_listing(user.id, uuid.uuid4())
        assert result is None

    async def test_list_by_user(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved)
        
        items, total = await repo.list_by_user(user.id, offset=0, limit=10)
        assert total >= 1
        assert len(items) >= 1
        assert items[0].user_id == user.id

    async def test_list_by_user_excludes_deleted(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved)
        
        saved.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()
        
        items, total = await repo.list_by_user(user.id, offset=0, limit=10)
        assert total == 0
        assert len(items) == 0

    async def test_duplicate_prevention(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved1 = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved1)
        
        existing = await repo.get_by_user_and_listing(user.id, test_listing.id)
        assert existing is not None
        assert existing.id == saved1.id
