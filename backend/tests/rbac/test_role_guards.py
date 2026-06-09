import pytest

from app.auth.permissions import BuiltinRole, PermissionKey
from app.auth.dependencies import require_permission, require_role


class TestRoleGuards:
    def test_builtin_roles_exist(self):
        roles = [r.value for r in BuiltinRole]
        assert "user" in roles
        assert "agency_admin" in roles
        assert "support_employee" in roles
        assert "platform_admin" in roles

    def test_no_duplicate_roles(self):
        roles = [r.value for r in BuiltinRole]
        assert len(roles) == len(set(roles))

    def test_no_duplicate_permission_keys(self):
        keys = [p.value for p in PermissionKey]
        assert len(keys) == len(set(keys))

    def test_permission_keys_exist(self):
        keys = [p.value for p in PermissionKey]
        assert "auth:login" in keys
        assert "auth:refresh" in keys
        assert "auth:logout" in keys
        assert "auth:password_reset" in keys
        assert "auth:session_revoke" in keys
        assert "auth:employee_deactivate" in keys
        assert "agency:read" in keys
        assert "agency:update" in keys
        assert "platform:read" in keys
        assert "platform:manage" in keys
        assert "system:admin" in keys
