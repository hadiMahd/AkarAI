from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agencies.models import AgencyTenant, AgencyProfile, AgencyEmployeeMembership
from app.common.repository import BaseRepository
from app.common.tenant import TenantContext


class AgencyProfileRepository(BaseRepository):
    async def get_by_tenant(self, tenant_id: UUID) -> Optional[AgencyProfile]:
        result = await self.session.execute(
            select(AgencyProfile).where(AgencyProfile.agency_tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create(self, profile: AgencyProfile) -> AgencyProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile


class AgencyEmployeeRepository(BaseRepository):
    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[AgencyEmployeeMembership], int]:
        count_q = select(func.count(AgencyEmployeeMembership.id)).where(
            AgencyEmployeeMembership.agency_tenant_id == tenant_id
        )
        total = (await self.session.execute(count_q)).scalar() or 0

        q = (
            select(AgencyEmployeeMembership)
            .where(AgencyEmployeeMembership.agency_tenant_id == tenant_id)
            .order_by(AgencyEmployeeMembership.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_by_id(self, membership_id: UUID) -> Optional[AgencyEmployeeMembership]:
        result = await self.session.execute(
            select(AgencyEmployeeMembership).where(AgencyEmployeeMembership.id == membership_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tenant_and_user(self, tenant_id: UUID, user_id: UUID) -> Optional[AgencyEmployeeMembership]:
        result = await self.session.execute(
            select(AgencyEmployeeMembership).where(
                AgencyEmployeeMembership.agency_tenant_id == tenant_id,
                AgencyEmployeeMembership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, membership: AgencyEmployeeMembership) -> AgencyEmployeeMembership:
        self.session.add(membership)
        await self.session.flush()
        return membership


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
