from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.common.tenant import TenantContext
from app.listings.models import Listing, ListingPhotoMetadata, SavedListing, ComparisonSession, ComparisonItem


class ListingRepository(BaseRepository):
    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Listing], int]:
        count_q = select(func.count(Listing.id)).where(Listing.agency_tenant_id == tenant_id)
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(Listing)
            .where(Listing.agency_tenant_id == tenant_id)
            .order_by(Listing.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_by_id(self, listing_id: UUID) -> Optional[Listing]:
        result = await self.session.execute(select(Listing).where(Listing.id == listing_id))
        return result.scalar_one_or_none()

    async def create(self, listing: Listing) -> Listing:
        self.session.add(listing)
        await self.session.flush()
        return listing


class ListingPhotoRepository(BaseRepository):
    async def list_by_listing(self, listing_id: UUID) -> list[ListingPhotoMetadata]:
        q = (
            select(ListingPhotoMetadata)
            .where(ListingPhotoMetadata.listing_id == listing_id)
            .order_by(ListingPhotoMetadata.display_order)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, photo_id: UUID) -> Optional[ListingPhotoMetadata]:
        result = await self.session.execute(
            select(ListingPhotoMetadata).where(ListingPhotoMetadata.id == photo_id)
        )
        return result.scalar_one_or_none()

    async def get_max_display_order(self, listing_id: UUID) -> int:
        q = select(func.coalesce(func.max(ListingPhotoMetadata.display_order), 0)).where(
            ListingPhotoMetadata.listing_id == listing_id
        )
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def create(self, photo: ListingPhotoMetadata) -> ListingPhotoMetadata:
        self.session.add(photo)
        await self.session.flush()
        return photo


class SavedListingRepository(BaseRepository):
    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list, int]:
        from app.listings.models import SavedListing
        count_q = select(func.count(SavedListing.id)).where(
            SavedListing.user_id == user_id,
            SavedListing.deleted_at.is_(None),
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(SavedListing)
            .where(SavedListing.user_id == user_id, SavedListing.deleted_at.is_(None))
            .order_by(SavedListing.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_by_user_and_listing(self, user_id: UUID, listing_id: UUID) -> Optional:
        from app.listings.models import SavedListing
        result = await self.session.execute(
            select(SavedListing).where(
                SavedListing.user_id == user_id,
                SavedListing.listing_id == listing_id,
                SavedListing.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, saved: SavedListing) -> SavedListing:
        self.session.add(saved)
        await self.session.flush()
        return saved


class ComparisonRepository(BaseRepository):
    async def list_sessions_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list, int]:
        from app.listings.models import ComparisonSession
        count_q = select(func.count(ComparisonSession.id)).where(
            ComparisonSession.user_id == user_id,
            ComparisonSession.deleted_at.is_(None),
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(ComparisonSession)
            .where(ComparisonSession.user_id == user_id, ComparisonSession.deleted_at.is_(None))
            .order_by(ComparisonSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_session_by_id(self, session_id: UUID) -> Optional:
        from app.listings.models import ComparisonSession
        result = await self.session.execute(
            select(ComparisonSession).where(ComparisonSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def create_session(self, session) -> ComparisonSession:
        self.session.add(session)
        await self.session.flush()
        return session

    async def list_items_by_session(self, session_id: UUID) -> list:
        from app.listings.models import ComparisonItem
        q = (
            select(ComparisonItem)
            .where(ComparisonItem.comparison_session_id == session_id)
            .order_by(ComparisonItem.position)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_item(self, session_id: UUID, listing_id: UUID) -> Optional:
        from app.listings.models import ComparisonItem
        result = await self.session.execute(
            select(ComparisonItem).where(
                ComparisonItem.comparison_session_id == session_id,
                ComparisonItem.listing_id == listing_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_item_count(self, session_id: UUID) -> int:
        from app.listings.models import ComparisonItem
        q = select(func.count(ComparisonItem.id)).where(
            ComparisonItem.comparison_session_id == session_id
        )
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def create_item(self, item) -> ComparisonItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def remove_item(self, item) -> None:
        await self.session.delete(item)
        await self.session.flush()
