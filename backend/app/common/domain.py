LISTING_STATUS_ACTIVE = "active"
LISTING_STATUS_INACTIVE = "inactive"
LISTING_STATUS_ARCHIVED = "archived"

LISTING_STATUS_TRANSITIONS = {
    "inactive": ["active"],
    "active": ["inactive", "archived"],
    "archived": [],
}

VALID_LISTING_STATUSES = frozenset([LISTING_STATUS_ACTIVE, LISTING_STATUS_INACTIVE, LISTING_STATUS_ARCHIVED])

LEAD_STATUS_NEW = "new"
LEAD_STATUS_REVIEWED = "reviewed"
LEAD_STATUS_CLOSED = "closed"

LEAD_STATUS_TRANSITIONS = {
    "new": ["reviewed", "closed"],
    "reviewed": ["closed"],
    "closed": [],
}

VALID_LEAD_STATUSES = frozenset([LEAD_STATUS_NEW, LEAD_STATUS_REVIEWED, LEAD_STATUS_CLOSED])

VIEWING_STATUS_SCHEDULED = "scheduled"
VIEWING_STATUS_CANCELLED_BY_USER = "cancelled_by_user"
VIEWING_STATUS_CANCELLED_BY_AGENCY = "cancelled_by_agency"
VIEWING_STATUS_COMPLETED = "completed"
VIEWING_STATUS_NO_SHOW = "no_show"

VIEWING_STATUS_TRANSITIONS = {
    "scheduled": ["cancelled_by_user", "cancelled_by_agency", "completed", "no_show"],
    "cancelled_by_user": [],
    "cancelled_by_agency": [],
    "completed": [],
    "no_show": [],
}

VALID_VIEWING_STATUSES = frozenset([
    VIEWING_STATUS_SCHEDULED,
    VIEWING_STATUS_CANCELLED_BY_USER,
    VIEWING_STATUS_CANCELLED_BY_AGENCY,
    VIEWING_STATUS_COMPLETED,
    VIEWING_STATUS_NO_SHOW,
])

PROPERTY_TYPES = frozenset(["apartment", "villa", "townhouse", "penthouse", "studio", "land", "commercial"])
LISTING_PURPOSES = frozenset(["sale", "rent"])
FURNISHING_OPTIONS = frozenset(["furnished", "unfurnished", "semi_furnished"])
AREA_UNITS = frozenset(["sqm", "sqft"])
VALID_SORT_OPTIONS = frozenset(["newest", "price_asc", "price_desc", "area_size_asc", "area_size_desc"])

MAX_COMPARISON_ITEMS = 4
