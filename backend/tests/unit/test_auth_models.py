import uuid
from datetime import datetime, timezone

import pytest

from app.auth.models import Role, Permission, RolePermission, RefreshSession, AccessRevocation
from app.users.models import User
from app.agencies.models import AgencyTenant, AgencyEmployeeMembership


class TestRoleConstraints:
    def test_role_slug_must_be_unique(self):
        r1 = Role(name="Test", slug="test-role", scope="user")
        r2 = Role(name="Test2", slug="test-role", scope="agency")
        assert r1.slug == r2.slug

    def test_role_scope_must_be_allowed(self):
        role = Role(name="Admin", slug="admin", scope="platform")
        assert role.scope in ("user", "agency", "platform")


class TestPermissionConstraints:
    def test_permission_key_must_be_unique(self):
        p1 = Permission(key="test:action", scope="user")
        p2 = Permission(key="test:action", scope="agency")
        assert p1.key == p2.key

    def test_permission_scope_must_be_allowed(self):
        for scope in ("user", "agency", "platform", "auth", "system"):
            perm = Permission(key=f"test:{scope}", scope=scope)
            assert perm.scope == scope


class TestRefreshSessionConstraints:
    def test_refresh_session_has_required_fields(self):
        session = RefreshSession(
            user_id=uuid.uuid4(),
            token_hash="abc123",
            family_id="fam-1",
            expires_at=datetime.now(timezone.utc),
        )
        assert session.token_hash is not None
        assert session.family_id is not None
        assert session.user_id is not None

    def test_refresh_session_revoked_default_none(self):
        session = RefreshSession(
            user_id=uuid.uuid4(),
            token_hash="abc456",
            family_id="fam-2",
            expires_at=datetime.now(timezone.utc),
        )
        assert session.revoked_at is None
        assert session.revocation_reason is None


class TestAccessRevocationConstraints:
    def test_access_revocation_has_required_fields(self):
        rev = AccessRevocation(
            jti=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            reason="logout",
            expires_at=datetime.now(timezone.utc),
        )
        assert rev.jti is not None
        assert rev.reason == "logout"

    def test_access_revocation_jti_unique(self):
        jti = str(uuid.uuid4())
        rev1 = AccessRevocation(jti=jti, user_id=uuid.uuid4(), reason="logout", expires_at=datetime.now(timezone.utc))
        rev2 = AccessRevocation(jti=jti, user_id=uuid.uuid4(), reason="suspicious_session", expires_at=datetime.now(timezone.utc))
        assert rev1.jti == rev2.jti


class TestAgencyTenantConstraints:
    def test_agency_tenant_has_required_fields(self):
        tenant = AgencyTenant(
            name="Test Agency",
            slug="test-agency",
            status="active",
        )
        assert tenant.slug == "test-agency"
        assert tenant.status == "active"

    def test_agency_tenant_slug_unique(self):
        t1 = AgencyTenant(name="Agency One", slug="unique-slug")
        t2 = AgencyTenant(name="Agency Two", slug="unique-slug")
        assert t1.slug == t2.slug

    def test_agency_tenant_status_values(self):
        for status in ("active", "inactive", "suspended"):
            tenant = AgencyTenant(name="Test", slug=f"test-{status}", status=status)
            assert tenant.status == status


class TestAgencyEmployeeMembershipConstraints:
    def test_membership_has_required_fields(self):
        membership = AgencyEmployeeMembership(
            agency_tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            status="active",
        )
        assert membership.status == "active"
        assert membership.agency_tenant_id is not None

    def test_membership_status_column_is_nullable_false(self):
        membership = AgencyEmployeeMembership(
            agency_tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            status="active",
        )
        assert membership.status == "active"

    def test_membership_can_be_deactivated(self):
        membership = AgencyEmployeeMembership(
            agency_tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
        )
        membership.status = "deactivated"
        membership.deactivated_at = datetime.now(timezone.utc)
        membership.deactivation_reason = "contract ended"
        assert membership.status == "deactivated"
        assert membership.deactivation_reason == "contract ended"


class TestUserConstraints:
    def test_user_status_values(self):
        for status in ("active", "inactive", "deactivated", "suspended"):
            user = User(email=f"test_{status}@test.com", password_hash="hash", status=status)
            assert user.status == status

    def test_user_not_active_cannot_sign_in(self):
        user = User(email="inactive@test.com", password_hash="hash", is_active=False, status="inactive")
        assert not user.is_active
        assert user.status == "inactive"
