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



class TestPermissionEvaluation:
    def test_auth_permissions_exist(self):
        auth_perms = [
            PermissionKey.AUTH_LOGIN,
            PermissionKey.AUTH_REFRESH,
            PermissionKey.AUTH_LOGOUT,
            PermissionKey.AUTH_PASSWORD_RESET,
        ]
        for perm in auth_perms:
            assert perm.value.startswith("auth:")

    def test_agency_permissions_exist(self):
        agency_perms = [
            PermissionKey.AGENCY_READ,
            PermissionKey.AGENCY_UPDATE,
        ]
        for perm in agency_perms:
            assert perm.value.startswith("agency:")

    def test_platform_permissions_exist(self):
        platform_perms = [
            PermissionKey.PLATFORM_READ,
            PermissionKey.PLATFORM_MANAGE,
        ]
        for perm in platform_perms:
            assert perm.value.startswith("platform:")

    def test_system_permissions_exist(self):
        assert PermissionKey.SYSTEM_ADMIN.value == "system:admin"

    def test_permission_keys_are_unique(self):
        keys = [p.value for p in PermissionKey]
        assert len(keys) == len(set(keys))
