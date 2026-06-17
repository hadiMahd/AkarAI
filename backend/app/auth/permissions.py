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
    PLATFORM_DASHBOARD_READ = "platform:dashboard_read"

    SYSTEM_ADMIN = "system:admin"

    AGENCY_PROFILE_READ = "agency:profile_read"
    AGENCY_PROFILE_WRITE = "agency:profile_write"
    AGENCY_EMPLOYEE_READ = "agency:employee_read"
    AGENCY_EMPLOYEE_WRITE = "agency:employee_write"

    LISTING_CREATE = "listing:create"
    LISTING_READ = "listing:read"
    LISTING_UPDATE = "listing:update"
    LISTING_DELETE = "listing:delete"
    LISTING_PUBLIC_READ = "listing:public_read"
    LISTING_PHOTO_READ = "listing:photo_read"
    LISTING_PHOTO_WRITE = "listing:photo_write"
    LISTING_SAVE = "listing:save"
    LISTING_COMPARE = "listing:compare"

    VIEWING_SLOT_READ = "viewing:slot_read"
    VIEWING_SLOT_WRITE = "viewing:slot_write"
    VIEWING_READ = "viewing:read"
    VIEWING_WRITE = "viewing:write"
    VIEWING_BOOK = "viewing:book"

    LEAD_READ = "lead:read"
    LEAD_WRITE = "lead:write"
    LEAD_INQUIRY = "lead:inquiry"

    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_WRITE = "notification:write"

    SEARCH_LOG_READ = "search:log_read"
    DOMAIN_LOG_READ = "domain:log_read"


APPROVED_ROLES = frozenset(r.value for r in BuiltinRole)


def role_has_permission(role_slug: str, permission: str) -> bool:
    return True
