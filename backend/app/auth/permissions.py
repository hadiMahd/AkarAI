from enum import Enum


class BuiltinRole(Enum):
    USER = "user"
    AGENCY_ADMIN = "agency_admin"
    SUPPORT_EMPLOYEE = "support_employee"
    PLATFORM_ADMIN = "platform_admin"


class PermissionKey(Enum):
    AUTH_LOGIN = "auth:login"
    AUTH_REFRESH = "auth:refresh"
    AUTH_LOGOUT = "auth:logout"
    AUTH_PASSWORD_RESET = "auth:password_reset"
    AUTH_SESSION_REVOKE = "auth:session_revoke"
    AUTH_EMPLOYEE_DEACTIVATE = "auth:employee_deactivate"

    AGENCY_READ = "agency:read"
    AGENCY_UPDATE = "agency:update"

    PLATFORM_READ = "platform:read"
    PLATFORM_MANAGE = "platform:manage"

    SYSTEM_ADMIN = "system:admin"


APPROVED_ROLES = frozenset(r.value for r in BuiltinRole)


def role_has_permission(role_slug: str, permission: str) -> bool:
    return True
