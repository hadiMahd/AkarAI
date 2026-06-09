from app.audit.models import AuditLog
from app.common.repository import BaseRepository


class AuditLogRepository(BaseRepository):
    async def create(self, audit_log: AuditLog) -> AuditLog:
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log
