from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.viewings.models import ListingViewingSlot, ScheduledViewing, ScheduledViewingStatusHistory


class ViewingSlotRepository(BaseRepository):
    async def list_active_by_listing(self, listing_id: UUID) -> list[ListingViewingSlot]:
        q = (
            select(ListingViewingSlot)
            .where(
                ListingViewingSlot.listing_id == listing_id,
                ListingViewingSlot.status == "active",
            )
            .order_by(ListingViewingSlot.starts_at)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def list_by_listing(self, listing_id: UUID) -> list[ListingViewingSlot]:
        q = (
            select(ListingViewingSlot)
            .where(ListingViewingSlot.listing_id == listing_id)
            .order_by(ListingViewingSlot.starts_at)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, slot_id: UUID) -> Optional[ListingViewingSlot]:
        result = await self.session.execute(
            select(ListingViewingSlot).where(ListingViewingSlot.id == slot_id)
        )
        return result.scalar_one_or_none()

    async def create(self, slot: ListingViewingSlot) -> ListingViewingSlot:
        self.session.add(slot)
        await self.session.flush()
        return slot

    async def increment_reserved_count(self, slot_id: UUID) -> Optional[ListingViewingSlot]:
        result = await self.session.execute(
            select(ListingViewingSlot).where(ListingViewingSlot.id == slot_id).with_for_update()
        )
        slot = result.scalar_one_or_none()
        if slot is None:
            return None
        slot.reserved_count = (slot.reserved_count or 0) + 1
        await self.session.flush()
        return slot


class ScheduledViewingRepository(BaseRepository):
    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[ScheduledViewing], int]:
        count_q = select(func.count(ScheduledViewing.id)).where(ScheduledViewing.user_id == user_id)
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(ScheduledViewing)
            .where(ScheduledViewing.user_id == user_id)
            .order_by(ScheduledViewing.scheduled_start_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20,
        status: Optional[str] = None,
        listing_id: Optional[UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> tuple[list[ScheduledViewing], int]:
        base_where = [ScheduledViewing.agency_tenant_id == tenant_id]

        if status is not None:
            base_where.append(ScheduledViewing.status == status)
        if listing_id is not None:
            base_where.append(ScheduledViewing.listing_id == listing_id)
        if date_from is not None:
            try:
                dt_from = datetime.fromisoformat(date_from)
                base_where.append(ScheduledViewing.scheduled_start_at >= dt_from)
            except ValueError:
                pass
        if date_to is not None:
            try:
                dt_to = datetime.fromisoformat(date_to)
                base_where.append(ScheduledViewing.scheduled_start_at <= dt_to)
            except ValueError:
                pass

        count_q = select(func.count(ScheduledViewing.id)).where(*base_where)
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(ScheduledViewing)
            .where(*base_where)
            .order_by(ScheduledViewing.scheduled_start_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_by_id(self, viewing_id: UUID) -> Optional[ScheduledViewing]:
        result = await self.session.execute(select(ScheduledViewing).where(ScheduledViewing.id == viewing_id))
        return result.scalar_one_or_none()

    async def create(self, viewing: ScheduledViewing) -> ScheduledViewing:
        self.session.add(viewing)
        await self.session.flush()
        return viewing


class ViewingStatusHistoryRepository(BaseRepository):
    async def create(self, history: ScheduledViewingStatusHistory) -> ScheduledViewingStatusHistory:
        self.session.add(history)
        await self.session.flush()
        return history
