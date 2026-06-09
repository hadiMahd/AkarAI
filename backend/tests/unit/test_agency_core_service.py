import uuid
from datetime import datetime, timezone

import pytest

from app.agencies.models import AgencyProfile, AgencyEmployeeMembership
from app.agencies.service import AgencyService
from app.common.exceptions import NotFoundError, ForbiddenError
from app.common.pagination import PaginationRequest
from app.common.tenant import TenantContext


def _make_tenant(tenant_id, actor_id, role="agency_admin"):
    return TenantContext(
        actor_id=actor_id,
        role=role,
        permissions=[],
        tenant_id=tenant_id,
    )


@pytest.mark.anyio
class TestAgencyServiceProfile:
    async def test_get_profile(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        profile = AgencyProfile(
            agency_tenant_id=test_tenant.id,
            display_name="Test Agency",
            legal_name="Test Agency LLC",
        )
        db_session.add(profile)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        fetched = await svc.get_profile()
        assert fetched.display_name == "Test Agency"
        assert fetched.legal_name == "Test Agency LLC"

    async def test_get_profile_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = AgencyService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Agency profile not found"):
            await svc.get_profile()

    async def test_update_profile(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        profile = AgencyProfile(
            agency_tenant_id=test_tenant.id,
            display_name="Old Name",
        )
        db_session.add(profile)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        updated = await svc.update_profile({
            "display_name": "New Name",
            "description": "Updated description",
        })
        assert updated.display_name == "New Name"
        assert updated.description == "Updated description"

    async def test_update_profile_creates_if_not_exists(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = AgencyService(db_session, ctx)
        updated = await svc.update_profile({"display_name": "Created Profile"})
        assert updated.display_name == "Created Profile"
        assert updated.agency_tenant_id == test_tenant.id

    async def test_update_profile_support_employee_forbidden(self, db_session, test_tenant, support_user):
        user, _ = support_user
        ctx = _make_tenant(test_tenant.id, user.id, role="support_employee")

        svc = AgencyService(db_session, ctx)
        with pytest.raises(ForbiddenError, match="Support employees cannot update"):
            await svc.update_profile({"display_name": "Should Fail"})

    async def test_get_profile_without_tenant_raises(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user

        svc = AgencyService(db_session, None)
        with pytest.raises(PermissionError):
            await svc.get_profile()


@pytest.mark.anyio
class TestAgencyServiceEmployees:
    async def test_list_employees(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1"))
        role_id = result.fetchone()[0]

        membership = AgencyEmployeeMembership(
            agency_tenant_id=test_tenant.id,
            user_id=user.id,
            role_id=role_id,
            status="active",
        )
        db_session.add(membership)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        result = await svc.list_employees(PaginationRequest(page=1, page_size=10))
        assert result.total >= 1

    async def test_get_employee(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1"))
        role_id = result.fetchone()[0]

        membership = AgencyEmployeeMembership(
            agency_tenant_id=test_tenant.id,
            user_id=user.id,
            role_id=role_id,
            status="active",
        )
        db_session.add(membership)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        fetched = await svc.get_employee(membership.id)
        assert fetched.id == membership.id

    async def test_get_employee_not_found(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        svc = AgencyService(db_session, ctx)
        with pytest.raises(NotFoundError, match="Employee not found"):
            await svc.get_employee(uuid.uuid4())

    async def test_create_employee(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'support_employee' LIMIT 1"))
        role_id = result.fetchone()[0]

        svc = AgencyService(db_session, ctx)
        membership = await svc.create_employee({
            "user_id": user.id,
            "role_id": role_id,
        })
        assert membership.status == "active"
        assert membership.agency_tenant_id == test_tenant.id

    async def test_create_employee_support_employee_forbidden(self, db_session, test_tenant, support_user):
        user, _ = support_user
        ctx = _make_tenant(test_tenant.id, user.id, role="support_employee")

        svc = AgencyService(db_session, ctx)
        with pytest.raises(ForbiddenError, match="Support employees cannot manage employees"):
            await svc.create_employee({"user_id": uuid.uuid4(), "role_id": uuid.uuid4()})

    async def test_update_employee(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1"))
        role_id = result.fetchone()[0]

        membership = AgencyEmployeeMembership(
            agency_tenant_id=test_tenant.id,
            user_id=user.id,
            role_id=role_id,
            status="active",
        )
        db_session.add(membership)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        updated = await svc.update_employee(membership.id, {"display_name": "Updated Name"})
        assert updated.display_name == "Updated Name"

    async def test_update_employee_support_employee_forbidden(self, db_session, test_tenant, support_user):
        user, _ = support_user
        ctx = _make_tenant(test_tenant.id, user.id, role="support_employee")

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'support_employee' LIMIT 1"))
        role_id = result.fetchone()[0]

        membership = AgencyEmployeeMembership(
            agency_tenant_id=test_tenant.id,
            user_id=user.id,
            role_id=role_id,
            status="active",
        )
        db_session.add(membership)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        with pytest.raises(ForbiddenError, match="Support employees cannot manage employees"):
            await svc.update_employee(membership.id, {"display_name": "Should Fail"})

    async def test_deactivate_employee(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1"))
        role_id = result.fetchone()[0]

        membership = AgencyEmployeeMembership(
            agency_tenant_id=test_tenant.id,
            user_id=user.id,
            role_id=role_id,
            status="active",
        )
        db_session.add(membership)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        await svc.deactivate_employee(membership.id)
        await db_session.refresh(membership)
        assert membership.status == "deactivated"

    async def test_deactivate_employee_support_employee_forbidden(self, db_session, test_tenant, support_user):
        user, _ = support_user
        ctx = _make_tenant(test_tenant.id, user.id, role="support_employee")

        from sqlalchemy import text
        result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'support_employee' LIMIT 1"))
        role_id = result.fetchone()[0]

        membership = AgencyEmployeeMembership(
            agency_tenant_id=test_tenant.id,
            user_id=user.id,
            role_id=role_id,
            status="active",
        )
        db_session.add(membership)
        await db_session.commit()

        svc = AgencyService(db_session, ctx)
        with pytest.raises(ForbiddenError, match="Support employees cannot manage employees"):
            await svc.deactivate_employee(membership.id)
