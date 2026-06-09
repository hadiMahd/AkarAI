from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository


class AuditService:
    def __init__(self, repository: AuditLogRepository):
        self._repo = repository

    async def log_event(self, entry: AuditLog) -> AuditLog:
        return await self._repo.create(entry)
