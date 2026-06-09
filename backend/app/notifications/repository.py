from app.common.repository import BaseRepository
from app.notifications.models import Notification


class NotificationRepository(BaseRepository):
    async def create(self, notification: Notification) -> Notification:
        self.session.add(notification)
        await self.session.flush()
        return notification
