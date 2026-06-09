import uuid
from datetime import datetime, timezone

import pytest

from app.common.exceptions import NotFoundError, ForbiddenError
from app.common.pagination import PaginationRequest
from app.notifications.models import Notification
from app.notifications.service import NotificationService


@pytest.mark.anyio
class TestNotificationServiceAccess:
    async def test_list_user_notifications(self, db_session, test_user):
        user, _ = test_user

        for i in range(3):
            n = Notification(
                recipient_user_id=user.id,
                channel="platform",
                template_key=f"test_{i}",
                status="pending",
            )
            db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        result = await svc.list_user_notifications(user.id, PaginationRequest(page=1, page_size=10))
        assert result.total >= 3
        assert len(result.items) >= 3

    async def test_get_notification(self, db_session, test_user):
        user, _ = test_user

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="test_get",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        fetched = await svc.get_notification(n.id, user.id)
        assert fetched.id == n.id
        assert fetched.template_key == "test_get"

    async def test_get_notification_not_found(self, db_session, test_user):
        user, _ = test_user
        svc = NotificationService(db_session)
        with pytest.raises(NotFoundError, match="Notification not found"):
            await svc.get_notification(uuid.uuid4(), user.id)

    async def test_get_notification_wrong_user(self, db_session, test_user):
        user, _ = test_user
        other_user_id = uuid.uuid4()

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="test_wrong_user",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        with pytest.raises(ForbiddenError, match="Not your notification"):
            await svc.get_notification(n.id, other_user_id)


@pytest.mark.anyio
class TestNotificationServiceState:
    async def test_mark_read(self, db_session, test_user):
        user, _ = test_user

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="test_read",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        updated = await svc.mark_read(n.id, user.id)
        assert updated.status == "read"
        assert updated.read_at is not None

    async def test_mark_read_not_found(self, db_session, test_user):
        user, _ = test_user
        svc = NotificationService(db_session)
        with pytest.raises(NotFoundError, match="Notification not found"):
            await svc.mark_read(uuid.uuid4(), user.id)

    async def test_mark_read_wrong_user(self, db_session, test_user):
        user, _ = test_user
        other_user_id = uuid.uuid4()

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="test_read_wrong",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        with pytest.raises(ForbiddenError, match="Not your notification"):
            await svc.mark_read(n.id, other_user_id)

    async def test_dismiss(self, db_session, test_user):
        user, _ = test_user

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="test_dismiss",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        updated = await svc.dismiss(n.id, user.id)
        assert updated.status == "dismissed"

    async def test_dismiss_not_found(self, db_session, test_user):
        user, _ = test_user
        svc = NotificationService(db_session)
        with pytest.raises(NotFoundError, match="Notification not found"):
            await svc.dismiss(uuid.uuid4(), user.id)

    async def test_dismiss_wrong_user(self, db_session, test_user):
        user, _ = test_user
        other_user_id = uuid.uuid4()

        n = Notification(
            recipient_user_id=user.id,
            channel="platform",
            template_key="test_dismiss_wrong",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        svc = NotificationService(db_session)
        with pytest.raises(ForbiddenError, match="Not your notification"):
            await svc.dismiss(n.id, other_user_id)

    async def test_create_notification(self, db_session, test_user):
        user, _ = test_user

        svc = NotificationService(db_session)
        n = await svc.create_notification({
            "recipient_user_id": user.id,
            "channel": "platform",
            "template_key": "welcome",
            "payload": {"message": "Hello"},
        })
        assert n.status == "pending"
        assert n.recipient_user_id == user.id
