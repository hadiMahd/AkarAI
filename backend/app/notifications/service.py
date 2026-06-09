from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError, ForbiddenError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.events import write_domain_event_log
from app.notifications.models import Notification
from app.notifications.repository import NotificationRepository


class NotificationService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = NotificationRepository(session)

    async def list_user_notifications(self, user_id: UUID, pagination: PaginationRequest) -> PaginationResult:
        items, total = await self._repo.list_by_user(
            user_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def get_notification(self, notification_id: UUID, user_id: UUID) -> Notification:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise NotFoundError(detail="Notification not found")
        if notification.recipient_user_id and str(notification.recipient_user_id) != str(user_id):
            raise ForbiddenError(detail="Not your notification")
        return notification

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> Notification:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise NotFoundError(detail="Notification not found")
        if notification.recipient_user_id and str(notification.recipient_user_id) != str(user_id):
            raise ForbiddenError(detail="Not your notification")
        notification.status = "read"
        notification.read_at = datetime.now(timezone.utc)
        await self._session.flush()
        await write_domain_event_log(
            self._session, "notification.read",
            aggregate_type="notification", aggregate_id=str(notification_id),
            actor_user_id=user_id,
        )
        return notification

    async def dismiss(self, notification_id: UUID, user_id: UUID) -> Notification:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise NotFoundError(detail="Notification not found")
        if notification.recipient_user_id and str(notification.recipient_user_id) != str(user_id):
            raise ForbiddenError(detail="Not your notification")
        notification.status = "dismissed"
        await self._session.flush()
        await write_domain_event_log(
            self._session, "notification.dismissed",
            aggregate_type="notification", aggregate_id=str(notification_id),
            actor_user_id=user_id,
        )
        return notification

    async def create_notification(self, data: dict) -> Notification:
        notification = Notification(
            recipient_user_id=data.get("recipient_user_id"),
            tenant_id=data.get("tenant_id"),
            channel=data.get("channel", "platform"),
            template_key=data.get("template_key"),
            payload=data.get("payload"),
            status="pending",
        )
        return await self._repo.create(notification)
