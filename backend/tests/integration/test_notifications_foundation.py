import pytest
from uuid import uuid4

import app.users.models  # noqa: F401
from app.common.database import async_session_factory
from app.notifications.models import Notification
from app.notifications.repository import NotificationRepository
from app.notifications.service import NotificationService


class TestNotificationsFoundation:
    @pytest.mark.integration
    async def test_create_notification(self):
        async with async_session_factory() as session:
            svc = NotificationService(session)

            created = await svc.create_notification({
                "channel": "email",
                "template_key": "welcome",
                "payload": {"message": "hello"},
            })
            assert created.id is not None
            assert created.channel == "email"
            await session.rollback()

    @pytest.mark.integration
    async def test_notification_persists(self):
        async with async_session_factory() as session:
            svc = NotificationService(session)
            created = await svc.create_notification({
                "channel": "system",
                "template_key": "test",
                "payload": {},
            })
            await session.commit()

            from sqlalchemy import select
            result = await session.execute(select(Notification).where(Notification.id == created.id))
            found = result.scalar_one()
            assert found.channel == "system"
