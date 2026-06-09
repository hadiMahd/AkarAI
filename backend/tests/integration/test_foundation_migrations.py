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
    "rag_documents",
    "rag_chunks",
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
    async def test_no_business_tables(self):
        async with async_session_factory() as session:
            for table in BUSINESS_TABLES:
                result = await session.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :name)"),
                    {"name": table},
                )
                exists = result.fetchone()[0]
                assert not exists, f"Business table '{table}' must not exist in Phase 2"
