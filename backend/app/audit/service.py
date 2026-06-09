from datetime import datetime, timezone
from uuid import UUID

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository


class AuditService:
    def __init__(self, repository: AuditLogRepository):
        self._repo = repository

    async def log_event(self, entry: AuditLog) -> AuditLog:
        return await self._repo.create(entry)

    async def log_auth_event(
        self,
        action: str,
        result: str,
        actor_user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            result=result,
            actor_user_id=actor_user_id,
            tenant_id=tenant_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        return await self._repo.create(entry)

    async def log_permission_denied(
        self,
        actor_user_id: UUID,
        required_permission: str,
        tenant_id: UUID | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return await self.log_auth_event(
            action="auth.permission_denied",
            result="denied",
            actor_user_id=actor_user_id,
            tenant_id=tenant_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"required_permission": required_permission},
        )

    async def log_tenant_denied(
        self,
        actor_user_id: UUID,
        attempted_tenant_id: UUID,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return await self.log_auth_event(
            action="auth.tenant_denied",
            result="denied",
            actor_user_id=actor_user_id,
            tenant_id=attempted_tenant_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"attempted_tenant": str(attempted_tenant_id)},
        )

    async def log_rate_limited(
        self,
        action: str,
        identifier: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return await self.log_auth_event(
            action="auth.rate_limited",
            result="denied",
            request_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"action": action, "identifier": identifier},
        )
