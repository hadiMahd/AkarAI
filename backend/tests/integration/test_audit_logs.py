import uuid

import pytest

import app.users.models  # noqa: F401  # ensure users table is registered for FK resolution
from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.audit.service import AuditService
from app.common.database import async_session_factory


class TestAuditLogs:
    @pytest.mark.integration
    async def test_create_audit_log(self):
        async with async_session_factory() as session:
            repo = AuditLogRepository(session)
            service = AuditService(repo)

            entry = AuditLog(
                request_id=str(uuid.uuid4()),
                action="test.action",
                resource_type="test",
                resource_id="1",
                result="success",
            )
            created = await service.log_event(entry)
            assert created.id is not None
            assert created.action == "test.action"
            await session.rollback()

    @pytest.mark.integration
    async def test_audit_log_persists(self):
        rid = str(uuid.uuid4())
        async with async_session_factory() as session:
            repo = AuditLogRepository(session)
            service = AuditService(repo)
            entry = AuditLog(request_id=rid, action="persist.test", result="success")
            await service.log_event(entry)
            await session.commit()

        async with async_session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(select(AuditLog).where(AuditLog.request_id == rid))
            found = result.scalar_one_or_none()
            assert found is not None
            assert found.action == "persist.test"
