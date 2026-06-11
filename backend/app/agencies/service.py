from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agencies.models import AgencyProfile, AgencyEmployeeMembership
from app.agencies.repository import AgencyProfileRepository, AgencyEmployeeRepository, AgenciesRepository
from app.common.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.tenant import TenantContext, require_tenant, ensure_tenant_match
from app.common.events import write_domain_event_log
from app.common.config import settings
from app.common.security import hash_password
from app.users.models import User
from app.users.repository import UsersRepository


class AgencyService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._profile_repo = AgencyProfileRepository(session, tenant)
        self._employee_repo = AgencyEmployeeRepository(session, tenant)

    async def get_profile(self) -> AgencyProfile:
        ctx = require_tenant(self._tenant)
        profile = await self._profile_repo.get_by_tenant(ctx.tenant_id)
        if profile is None:
            raise NotFoundError(detail="Agency profile not found")
        return profile

    async def update_profile(self, data: dict) -> AgencyProfile:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot update agency profile")
        profile = await self._profile_repo.get_by_tenant(ctx.tenant_id)
        if profile is None:
            profile = AgencyProfile(agency_tenant_id=ctx.tenant_id, display_name="")
            self._session.add(profile)

        if "display_name" in data and data["display_name"] is not None:
            profile.display_name = data["display_name"]
        if "legal_name" in data:
            profile.legal_name = data["legal_name"]
        if "description" in data:
            profile.description = data["description"]
        if "phone" in data:
            profile.phone = data["phone"]
        if "email" in data:
            profile.email = data["email"]
        if "website_url" in data:
            profile.website_url = data["website_url"]
        if "address" in data:
            profile.address = data["address"]
        if "city" in data:
            profile.city = data["city"]
        if "country" in data:
            profile.country = data["country"]
        if "status" in data and data["status"] is not None:
            profile.status = data["status"]

        await self._session.flush()
        await write_domain_event_log(
            self._session, "agency.profile_updated",
            aggregate_type="agency", aggregate_id=str(ctx.tenant_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
        )
        return profile

    async def list_employees(self, pagination: PaginationRequest) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._employee_repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def get_employee(self, employee_id: UUID) -> AgencyEmployeeMembership:
        ctx = require_tenant(self._tenant)
        membership = await self._employee_repo.get_by_id(employee_id)
        if membership is None:
            raise NotFoundError(detail="Employee not found")
        ensure_tenant_match(self._tenant, membership.agency_tenant_id)
        return membership

    async def create_employee(self, data: dict) -> AgencyEmployeeMembership:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot manage employees")

        work_email = data.get("work_email")
        role_slug = data.get("role_slug")
        display_name = data.get("display_name")

        if not work_email:
            raise ValidationError(detail="work_email is required")
        if not display_name:
            raise ValidationError(detail="display_name is required")
        if role_slug != "support_employee":
            raise ValidationError(detail="Only support_employee can be created from this flow")

        users_repo = UsersRepository(self._session)
        existing_user = await users_repo.get_user_by_email(work_email)
        if existing_user is not None:
            raise ValidationError(detail="A user account with this email already exists")

        from app.auth.models import Role
        from sqlalchemy import select

        result = await self._session.execute(
            select(Role).where(Role.slug == "support_employee")
        )
        role = result.scalar_one_or_none()
        if role is None:
            raise ValidationError(detail="support_employee role is not configured")

        new_user = User(
            email=work_email,
            name=display_name,
            password_hash=hash_password(settings.agency_employee_initial_password),
            role_id=role.id,
            is_active=True,
            status="active",
        )
        new_user = await users_repo.create_user(new_user)

        membership = AgencyEmployeeMembership(
            agency_tenant_id=ctx.tenant_id,
            user_id=new_user.id,
            role_id=role.id,
            status="active",
            display_name=display_name,
            work_email=work_email,
        )
        membership = await self._employee_repo.create(membership)
        await write_domain_event_log(
            self._session, "agency.employee_added",
            aggregate_type="employee", aggregate_id=str(membership.id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"user_id": str(new_user.id), "role_id": str(role.id), "email": work_email},
        )
        return membership

    async def update_employee(self, employee_id: UUID, data: dict) -> AgencyEmployeeMembership:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot manage employees")

        membership = await self._employee_repo.get_by_id(employee_id)
        if membership is None:
            raise NotFoundError(detail="Employee not found")
        ensure_tenant_match(self._tenant, membership.agency_tenant_id)

        if data.get("role_id") is not None:
            membership.role_id = data["role_id"]
        if data.get("display_name") is not None:
            membership.display_name = data.get("display_name")
        if data.get("work_email") is not None:
            membership.work_email = data.get("work_email")

        await self._session.flush()
        await write_domain_event_log(
            self._session, "agency.employee_updated",
            aggregate_type="employee", aggregate_id=str(employee_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
        )
        return membership

    async def deactivate_employee(self, employee_id: UUID) -> None:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot manage employees")

        membership = await self._employee_repo.get_by_id(employee_id)
        if membership is None:
            raise NotFoundError(detail="Employee not found")
        ensure_tenant_match(self._tenant, membership.agency_tenant_id)

        membership.status = "deactivated"
        await self._session.flush()
        await write_domain_event_log(
            self._session, "agency.employee_deactivated",
            aggregate_type="employee", aggregate_id=str(employee_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
        )


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
