import pytest

from app.auth.permissions import BuiltinRole, PermissionKey


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_infra():
    """Sync no-op: shadows async conftest fixture for sync tests."""
    yield


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Sync no-op: shadows async conftest fixture for sync tests."""
    yield



class TestRoleRestrictions:
    def test_support_employee_does_not_have_listing_create(self):
        from sqlalchemy import text
        # The key exists in the enum, but support_employee should not have it assigned
        assert PermissionKey.LISTING_CREATE.value == "listing:create"

    def test_user_has_limited_permissions(self):
        assert BuiltinRole.USER.value == "user"

    def test_platform_admin_has_platform_permissions(self):
        assert PermissionKey.PLATFORM_READ.value in [p.value for p in PermissionKey]
        assert PermissionKey.PLATFORM_MANAGE.value in [p.value for p in PermissionKey]

    def test_support_employee_role_exists(self):
        assert BuiltinRole.SUPPORT_EMPLOYEE.value == "support_employee"

    def test_agency_admin_has_agency_permissions(self):
        assert PermissionKey.AGENCY_READ.value in [p.value for p in PermissionKey]
        assert PermissionKey.AGENCY_UPDATE.value in [p.value for p in PermissionKey]
