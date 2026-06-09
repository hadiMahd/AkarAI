from app.notifications.models import Notification
from app.notifications.repository import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self._repo = repository

    async def create_notification(self, notification: Notification) -> Notification:
        return await self._repo.create(notification)
