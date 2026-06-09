import pytest
import uuid
from datetime import datetime, timezone

from app.listings.models import ComparisonSession, ComparisonItem
from app.listings.repository import ComparisonRepository
from app.common.domain import MAX_COMPARISON_ITEMS


@pytest.mark.anyio
class TestComparisonRepository:
    async def test_create_comparison_session(self, db_session, test_user):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        result = await repo.create_session(session)
        
        assert result.id is not None
        assert result.user_id == user.id
        assert result.name == "Test Comparison"
        assert result.deleted_at is None

    async def test_get_session_by_id(self, db_session, test_user):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        result = await repo.get_session_by_id(session.id)
        assert result is not None
        assert result.id == session.id
        assert result.user_id == user.id

    async def test_get_session_by_id_not_found(self, db_session):
        repo = ComparisonRepository(db_session)
        
        result = await repo.get_session_by_id(uuid.uuid4())
        assert result is None

    async def test_list_sessions_by_user(self, db_session, test_user):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        items, total = await repo.list_sessions_by_user(user.id, offset=0, limit=10)
        assert total >= 1
        assert len(items) >= 1
        assert items[0].user_id == user.id

    async def test_list_sessions_excludes_deleted(self, db_session, test_user):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        session.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()
        
        items, total = await repo.list_sessions_by_user(user.id, offset=0, limit=10)
        assert total == 0
        assert len(items) == 0

    async def test_create_comparison_item(self, db_session, test_user, test_listing):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        item = ComparisonItem(
            comparison_session_id=session.id,
            listing_id=test_listing.id,
            position=0,
        )
        result = await repo.create_item(item)
        
        assert result.id is not None
        assert result.comparison_session_id == session.id
        assert result.listing_id == test_listing.id

    async def test_get_item(self, db_session, test_user, test_listing):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        item = ComparisonItem(
            comparison_session_id=session.id,
            listing_id=test_listing.id,
            position=0,
        )
        await repo.create_item(item)
        
        result = await repo.get_item(session.id, test_listing.id)
        assert result is not None
        assert result.comparison_session_id == session.id
        assert result.listing_id == test_listing.id

    async def test_get_item_count(self, db_session, test_user, test_listing):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        item = ComparisonItem(
            comparison_session_id=session.id,
            listing_id=test_listing.id,
            position=0,
        )
        await repo.create_item(item)
        
        count = await repo.get_item_count(session.id)
        assert count == 1

    async def test_remove_item(self, db_session, test_user, test_listing):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        item = ComparisonItem(
            comparison_session_id=session.id,
            listing_id=test_listing.id,
            position=0,
        )
        await repo.create_item(item)
        
        await repo.remove_item(item)
        
        result = await repo.get_item(session.id, test_listing.id)
        assert result is None

    async def test_four_item_limit(self, db_session, test_user, test_tenant):
        user, _ = test_user
        repo = ComparisonRepository(db_session)
        
        session = ComparisonSession(user_id=user.id, name="Test Comparison")
        await repo.create_session(session)
        
        from app.listings.models import Listing
        for i in range(MAX_COMPARISON_ITEMS):
            listing = Listing(
                agency_tenant_id=test_tenant.id,
                title=f"Test Listing {i}",
                description=f"Description {i}",
                property_type="apartment",
                listing_purpose="sale",
                price=100000 + i * 10000,
                currency="USD",
                bedrooms=2,
                bathrooms=1,
                area_size=80.0,
                area_unit="sqm",
                furnishing="furnished",
                location_text="Test City",
                address=f"{i} Test St",
                city="Test City",
                country="Test Country",
                status="active",
            )
            db_session.add(listing)
            await db_session.flush()
            
            item = ComparisonItem(
                comparison_session_id=session.id,
                listing_id=listing.id,
                position=i,
            )
            await repo.create_item(item)
        
        count = await repo.get_item_count(session.id)
        assert count == MAX_COMPARISON_ITEMS
