import pytest
from sqlalchemy import text


class TestPhase4Migrations:
    async def test_agency_profiles_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'agency_profiles')")
        )
        assert result.scalar() is True

    async def test_listings_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'listings')")
        )
        assert result.scalar() is True

    async def test_listing_photo_metadata_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'listing_photo_metadata')")
        )
        assert result.scalar() is True

    async def test_listing_viewing_slots_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'listing_viewing_slots')")
        )
        assert result.scalar() is True

    async def test_scheduled_viewings_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scheduled_viewings')")
        )
        assert result.scalar() is True

    async def test_scheduled_viewing_status_history_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scheduled_viewing_status_history')")
        )
        assert result.scalar() is True

    async def test_saved_listings_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'saved_listings')")
        )
        assert result.scalar() is True

    async def test_comparison_sessions_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'comparison_sessions')")
        )
        assert result.scalar() is True

    async def test_comparison_items_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'comparison_items')")
        )
        assert result.scalar() is True

    async def test_leads_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'leads')")
        )
        assert result.scalar() is True

    async def test_lead_spam_results_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'lead_spam_results')")
        )
        assert result.scalar() is True

    async def test_lead_level_results_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'lead_level_results')")
        )
        assert result.scalar() is True

    async def test_lead_suggested_replies_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'lead_suggested_replies')")
        )
        assert result.scalar() is True

    async def test_reviewed_lead_records_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'reviewed_lead_records')")
        )
        assert result.scalar() is True

    async def test_search_logs_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'search_logs')")
        )
        assert result.scalar() is True

    async def test_domain_event_logs_table_exists(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'domain_event_logs')")
        )
        assert result.scalar() is True

    async def test_notifications_has_read_at_column(self, async_client, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'read_at')")
        )
        assert result.scalar() is True
