from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.agencies.models import AgencyTenant, AgencyEmployeeMembership


class AgenciesRepository(BaseRepository):
    async def get_tenant_by_id(self, tenant_id: str) -> AgencyTenant | None:
        result = await self.session.execute(
            select(AgencyTenant).where(AgencyTenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_membership(self, tenant_id: str, user_id: str) -> AgencyEmployeeMembership | None:
        result = await self.session.execute(
            select(AgencyEmployeeMembership).where(
                AgencyEmployeeMembership.agency_tenant_id == tenant_id,
                AgencyEmployeeMembership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_memberships_for_user(self, user_id: str) -> list[AgencyEmployeeMembership]:
        result = await self.session.execute(
            select(AgencyEmployeeMembership).where(
                AgencyEmployeeMembership.user_id == user_id,
                AgencyEmployeeMembership.status == "active",
            )
        )
        return list(result.scalars().all())

    async def update_membership(self, membership: AgencyEmployeeMembership) -> AgencyEmployeeMembership:
        self.session.add(membership)
        await self.session.flush()
        return membership
