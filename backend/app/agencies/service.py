from datetime import datetime, timezone
from uuid import UUID

from app.agencies.models import AgencyEmployeeMembership
from app.agencies.repository import AgenciesRepository


class AgenciesService:
    def __init__(self, repository: AgenciesRepository):
        self._repo = repository

    async def deactivate_employee(
        self,
        membership: AgencyEmployeeMembership,
        deactivated_by_user_id: UUID,
        reason: str,
    ) -> AgencyEmployeeMembership:
        membership.status = "deactivated"
        membership.deactivated_at = datetime.now(timezone.utc)
        membership.deactivated_by_user_id = deactivated_by_user_id
        membership.deactivation_reason = reason
        return await self._repo.update_membership(membership)

    async def is_tenant_active(self, tenant_id: str) -> bool:
        tenant = await self._repo.get_tenant_by_id(tenant_id)
        if tenant is None:
            return False
        return tenant.status == "active"
