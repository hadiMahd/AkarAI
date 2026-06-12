from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.repository import BaseRepository
from app.common.tenant import TenantContext
from app.listings.models import Listing, ListingPhotoMetadata, ListingPhotoDerivative, SavedListing, ComparisonSession, ComparisonItem


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

    async def update_status(self, photo_id: UUID, status: str) -> None:
        await self.session.execute(
            update(ListingPhotoMetadata).where(ListingPhotoMetadata.id == photo_id).values(status=status)
        )

    async def update_processing_fields(
        self,
        photo_id: UUID,
        *,
        content_type: str | None = None,
        file_size_bytes: int | None = None,
        width: int | None = None,
        height: int | None = None,
        moderation_label: str | None = None,
        moderation_score: float | None = None,
        quality_score: float | None = None,
        status: str | None = None,
    ) -> None:
        from decimal import Decimal
        values = {}
        if content_type is not None:
            values["content_type"] = content_type
        if file_size_bytes is not None:
            values["file_size_bytes"] = file_size_bytes
        if width is not None:
            values["width"] = width
        if height is not None:
            values["height"] = height
        if moderation_label is not None:
            values["moderation_label"] = moderation_label
        if moderation_score is not None:
            values["moderation_score"] = Decimal(str(moderation_score))
        if quality_score is not None:
            values["quality_score"] = Decimal(str(quality_score))
        if status is not None:
            values["status"] = status
        if values:
            await self.session.execute(
                update(ListingPhotoMetadata).where(ListingPhotoMetadata.id == photo_id).values(**values)
            )

    async def get_first_public_safe_for_listings(self, listing_ids: list[UUID]) -> dict[UUID, ListingPhotoMetadata]:
        if not listing_ids:
            return {}
        q = (
            select(ListingPhotoMetadata)
            .join(
                ListingPhotoDerivative,
                ListingPhotoDerivative.listing_photo_metadata_id == ListingPhotoMetadata.id,
            )
            .where(
                ListingPhotoMetadata.listing_id.in_(listing_ids),
                ListingPhotoDerivative.is_public_safe.is_(True),
            )
            .order_by(
                ListingPhotoMetadata.listing_id,
                ListingPhotoMetadata.display_order,
                ListingPhotoDerivative.created_at,
            )
        )
        result = await self.session.execute(q)
        photos = list(result.scalars().all())
        first: dict[UUID, ListingPhotoMetadata] = {}
        for p in photos:
            if p.listing_id not in first:
                first[p.listing_id] = p
        return first

    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[ListingPhotoMetadata], int]:
        count_q = select(func.count(ListingPhotoMetadata.id)).where(
            ListingPhotoMetadata.agency_tenant_id == tenant_id
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(ListingPhotoMetadata)
            .where(ListingPhotoMetadata.agency_tenant_id == tenant_id)
            .order_by(ListingPhotoMetadata.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total


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

    async def list_by_user_with_details(
        self, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list, int]:
        from app.listings.models import SavedListing, Listing
        count_q = (
            select(func.count(SavedListing.id))
            .join(Listing, SavedListing.listing_id == Listing.id)
            .where(
                SavedListing.user_id == user_id,
                SavedListing.deleted_at.is_(None),
                Listing.status == "active",
            )
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(SavedListing, Listing)
            .join(Listing, SavedListing.listing_id == Listing.id)
            .where(SavedListing.user_id == user_id, SavedListing.deleted_at.is_(None), Listing.status == "active")
            .order_by(SavedListing.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        rows = result.all()
        return [
            type("SavedListingWithListing", (), {"saved": row[0], "listing": row[1]})
            for row in rows
        ], total

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


class ListingPhotoDerivativeRepository(BaseRepository):
    async def list_by_photo(self, photo_id: UUID) -> list[ListingPhotoDerivative]:
        q = (
            select(ListingPhotoDerivative)
            .where(ListingPhotoDerivative.listing_photo_metadata_id == photo_id)
            .order_by(ListingPhotoDerivative.created_at)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, derivative_id: UUID) -> Optional[ListingPhotoDerivative]:
        result = await self.session.execute(
            select(ListingPhotoDerivative).where(ListingPhotoDerivative.id == derivative_id)
        )
        return result.scalar_one_or_none()

    async def get_public_safe_by_photo(self, photo_id: UUID) -> Optional[ListingPhotoDerivative]:
        result = await self.session.execute(
            select(ListingPhotoDerivative).where(
                ListingPhotoDerivative.listing_photo_metadata_id == photo_id,
                ListingPhotoDerivative.is_public_safe == True,
            )
        )
        return result.scalars().first()

    async def list_public_safe_by_photos(self, photo_ids: list[UUID]) -> list[ListingPhotoDerivative]:
        if not photo_ids:
            return []
        q = (
            select(ListingPhotoDerivative)
            .where(
                ListingPhotoDerivative.listing_photo_metadata_id.in_(photo_ids),
                ListingPhotoDerivative.is_public_safe == True,
            )
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def create(self, derivative: ListingPhotoDerivative) -> ListingPhotoDerivative:
        self.session.add(derivative)
        await self.session.flush()
        return derivative
