from app.auth.permissions import BuiltinRole, PermissionKey


class TestPermissions:
    def test_builtin_roles_exist(self):
        roles = [r.value for r in BuiltinRole]
        assert "user" in roles
        assert "agency_admin" in roles
        assert "support_employee" in roles
        assert "platform_admin" in roles

    def test_permission_keys_exist(self):
        keys = [p.value for p in PermissionKey]
        assert "user:read" in keys
        assert "listing:create" in keys
        assert "lead:create" in keys
        assert "viewing:create" in keys
        assert "system:admin" in keys

    def test_no_duplicate_permission_keys(self):
        keys = [p.value for p in PermissionKey]
        assert len(keys) == len(set(keys))

    def test_no_duplicate_roles(self):
        roles = [r.value for r in BuiltinRole]
        assert len(roles) == len(set(roles))
