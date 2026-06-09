import pytest


class TestPhase4DomainConstants:
    def test_listing_statuses_defined(self):
        from app.common.domain import VALID_LISTING_STATUSES, LISTING_STATUS_ACTIVE, LISTING_STATUS_INACTIVE, LISTING_STATUS_ARCHIVED
        assert LISTING_STATUS_ACTIVE == "active"
        assert LISTING_STATUS_INACTIVE == "inactive"
        assert LISTING_STATUS_ARCHIVED == "archived"
        assert len(VALID_LISTING_STATUSES) == 3

    def test_listing_status_transitions(self):
        from app.common.domain import LISTING_STATUS_TRANSITIONS
        assert "active" in LISTING_STATUS_TRANSITIONS["inactive"]
        assert "inactive" in LISTING_STATUS_TRANSITIONS["active"]
        assert "archived" in LISTING_STATUS_TRANSITIONS["active"]
        assert LISTING_STATUS_TRANSITIONS["archived"] == []

    def test_lead_statuses_defined(self):
        from app.common.domain import VALID_LEAD_STATUSES, LEAD_STATUS_NEW, LEAD_STATUS_REVIEWED, LEAD_STATUS_CLOSED
        assert LEAD_STATUS_NEW == "new"
        assert LEAD_STATUS_REVIEWED == "reviewed"
        assert LEAD_STATUS_CLOSED == "closed"
        assert len(VALID_LEAD_STATUSES) == 3

    def test_lead_status_transitions(self):
        from app.common.domain import LEAD_STATUS_TRANSITIONS
        assert "reviewed" in LEAD_STATUS_TRANSITIONS["new"]
        assert "closed" in LEAD_STATUS_TRANSITIONS["new"]
        assert "closed" in LEAD_STATUS_TRANSITIONS["reviewed"]
        assert LEAD_STATUS_TRANSITIONS["closed"] == []

    def test_viewing_statuses_defined(self):
        from app.common.domain import VALID_VIEWING_STATUSES
        assert len(VALID_VIEWING_STATUSES) == 5

    def test_viewing_status_transitions(self):
        from app.common.domain import VIEWING_STATUS_TRANSITIONS
        assert "cancelled_by_user" in VIEWING_STATUS_TRANSITIONS["scheduled"]
        assert "completed" in VIEWING_STATUS_TRANSITIONS["scheduled"]
        assert "no_show" in VIEWING_STATUS_TRANSITIONS["scheduled"]

    def test_max_comparison_items(self):
        from app.common.domain import MAX_COMPARISON_ITEMS
        assert MAX_COMPARISON_ITEMS == 4

    def test_sort_options_defined(self):
        from app.common.domain import VALID_SORT_OPTIONS
        assert "newest" in VALID_SORT_OPTIONS
        assert "price_asc" in VALID_SORT_OPTIONS
        assert "price_desc" in VALID_SORT_OPTIONS
        assert "area_size_asc" in VALID_SORT_OPTIONS
        assert "area_size_desc" in VALID_SORT_OPTIONS


class TestPhase4RateLimits:
    def test_phase4_rate_limits_defined(self):
        from app.common.rate_limit import PHASE4_RATE_LIMITS
        assert "search" in PHASE4_RATE_LIMITS
        assert "inquiry" in PHASE4_RATE_LIMITS
        assert "viewing_booking" in PHASE4_RATE_LIMITS

    def test_search_rate_limit_reasonable(self):
        from app.common.rate_limit import PHASE4_RATE_LIMITS
        limits = PHASE4_RATE_LIMITS["search"]
        assert limits["max_requests"] > 0
        assert limits["window_seconds"] > 0

    def test_inquiry_rate_limit_strict(self):
        from app.common.rate_limit import PHASE4_RATE_LIMITS
        limits = PHASE4_RATE_LIMITS["inquiry"]
        assert limits["max_requests"] == 5
        assert limits["window_seconds"] == 600


class TestPhase4PermissionKeys:
    def test_all_phase4_permission_keys_defined(self):
        from app.auth.permissions import PermissionKey
        phase4_keys = [
            "agency:profile_read", "agency:profile_write",
            "agency:employee_read", "agency:employee_write",
            "listing:create", "listing:read", "listing:update", "listing:delete",
            "listing:public_read", "listing:photo_read", "listing:photo_write",
            "listing:save", "listing:compare",
            "viewing:slot_read", "viewing:slot_write",
            "viewing:read", "viewing:write", "viewing:book",
            "lead:read", "lead:write", "lead:inquiry",
            "notification:read", "notification:write",
            "search:log_read", "domain:log_read",
        ]
        for key in phase4_keys:
            assert key in [p.value for p in PermissionKey], f"Missing {key}"


class TestDomainConstants:
    def test_property_types_defined(self):
        from app.common.domain import PROPERTY_TYPES
        assert "apartment" in PROPERTY_TYPES
        assert "villa" in PROPERTY_TYPES

    def test_listing_purposes_defined(self):
        from app.common.domain import LISTING_PURPOSES
        assert "sale" in LISTING_PURPOSES
        assert "rent" in LISTING_PURPOSES
