from enum import Enum


class BuiltinRole(Enum):
    USER = "user"
    AGENCY_ADMIN = "agency_admin"
    SUPPORT_EMPLOYEE = "support_employee"
    PLATFORM_ADMIN = "platform_admin"


class PermissionKey(Enum):
    # User permissions
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Listing permissions
    LISTING_CREATE = "listing:create"
    LISTING_READ = "listing:read"
    LISTING_UPDATE = "listing:update"
    LISTING_DELETE = "listing:delete"

    # Lead permissions
    LEAD_CREATE = "lead:create"
    LEAD_READ = "lead:read"
    LEAD_UPDATE = "lead:update"

    # Viewing permissions
    VIEWING_CREATE = "viewing:create"
    VIEWING_READ = "viewing:read"
    VIEWING_CANCEL = "viewing:cancel"

    # Agency permissions
    AGENCY_READ = "agency:read"
    AGENCY_UPDATE = "agency:update"

    # Platform permissions
    PLATFORM_READ = "platform:read"
    PLATFORM_MANAGE = "platform:manage"

    # System permissions
    SYSTEM_ADMIN = "system:admin"
