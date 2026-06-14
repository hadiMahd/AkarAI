import pytest
from sqlalchemy import text

from app.common.database import async_session_factory

FOUNDATION_TABLES = [
    "roles",
    "permissions",
    "role_permissions",
    "users",
    "refresh_sessions",
    "audit_logs",
    "outbox_events",
    "inbox_events",
    "notifications",
]

BUSINESS_TABLES = [
    "listings",
    "leads",
    "viewings",
    "agency_profiles",
    "media",
    "listing_images",
    "scheduled_viewings",
]


class TestFoundationMigrations:
    @pytest.mark.integration
    async def test_foundation_tables_exist(self):
        async with async_session_factory() as session:
            for table in FOUNDATION_TABLES:
                result = await session.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :name)"),
                    {"name": table},
                )
                exists = result.fetchone()[0]
                assert exists, f"Foundation table '{table}' should exist after migration"

    @pytest.mark.integration
    async def test_no_business_tables_in_phase2(self):
        phase4_tables = frozenset([
            "listings", "leads", "agency_profiles", "scheduled_viewings",
            "listing_viewing_slots", "listing_photo_metadata",
            "scheduled_viewing_status_history", "saved_listings",
            "comparison_sessions", "comparison_items", "search_logs",
            "domain_event_logs", "reviewed_lead_records",
            "lead_spam_results", "lead_level_results", "lead_suggested_replies",
        ])
        async with async_session_factory() as session:
            for table in BUSINESS_TABLES:
                if table in phase4_tables:
                    continue
                result = await session.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :name)"),
                    {"name": table},
                )
                exists = result.fetchone()[0]
                assert not exists, f"Business table '{table}' must not exist in Phase 4"
