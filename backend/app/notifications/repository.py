from typing import Optional
from uuid import UUID

from sqlalchemy import select, func

from app.common.repository import BaseRepository
from app.notifications.models import Notification


class NotificationRepository(BaseRepository):
    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Notification], int]:
        count_q = select(func.count(Notification.id)).where(
            Notification.recipient_user_id == user_id
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        q = (
            select(Notification)
            .where(Notification.recipient_user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def create(self, notification: Notification) -> Notification:
        self.session.add(notification)
        await self.session.flush()
        return notification
