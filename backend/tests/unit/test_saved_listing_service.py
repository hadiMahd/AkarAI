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

    async def test_list_by_user_with_details_returns_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved)
        
        rows, total = await repo.list_by_user_with_details(user.id, offset=0, limit=10)
        assert total >= 1
        assert len(rows) >= 1
        row = rows[0]
        assert row.saved.user_id == user.id
        assert row.saved.listing_id == test_listing.id
        assert row.listing.id == test_listing.id
        assert row.listing.status == "active"
        assert row.saved.deleted_at is None

    async def test_list_by_user_with_details_excludes_deleted_saved(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved)
        saved.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()
        
        rows, total = await repo.list_by_user_with_details(user.id, offset=0, limit=10)
        assert total == 0
        assert len(rows) == 0

    async def test_list_by_user_with_details_excludes_inactive_listing(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        test_listing.status = "inactive"
        await db_session.flush()
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved)
        
        rows, total = await repo.list_by_user_with_details(user.id, offset=0, limit=10)
        assert total == 0
        assert len(rows) == 0

    async def test_list_by_user_with_details_response_shaping(self, db_session, test_tenant, agency_admin_user, test_listing):
        """Verify the response data can be properly shaped into SavedListingWithDetailsResponse without crashing."""
        from app.listings.schemas import PublicListingResponse, SavedListingWithDetailsResponse
        
        user, _ = agency_admin_user
        repo = SavedListingRepository(db_session)
        
        saved = SavedListing(user_id=user.id, listing_id=test_listing.id)
        await repo.create(saved)
        
        rows, total = await repo.list_by_user_with_details(user.id, offset=0, limit=10)
        assert total >= 1
        
        listing_responses: list[PublicListingResponse] = []
        for row in rows:
            listing_resp = PublicListingResponse.model_validate(row.listing)
            listing_responses.append(listing_resp)
        
        items: list[SavedListingWithDetailsResponse] = []
        for row, listing_resp in zip(rows, listing_responses):
            items.append(
                SavedListingWithDetailsResponse(
                    id=row.saved.id,
                    user_id=row.saved.user_id,
                    listing_id=row.saved.listing_id,
                    created_at=row.saved.created_at,
                    deleted_at=row.saved.deleted_at,
                    listing=listing_resp,
                )
            )
        
        assert len(items) == total
        assert items[0].listing.id == test_listing.id
        assert items[0].listing.title == "Test Listing"
