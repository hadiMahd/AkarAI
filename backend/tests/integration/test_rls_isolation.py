"""Tests for PostgreSQL Row-Level Security tenant/user isolation.

These tests prove that raw DB/repository access cannot cross tenant or user
boundaries when RLS context is set or missing.

Tests connect via the non-superuser 'akarai' so RLS policies take effect.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text

from app.common.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

_pg_engine = None
_app_engine = None


def _superuser_factory():
    global _pg_engine
    if _pg_engine is None:
        url = settings.pgbouncer_database_url.replace(
            "pgbouncer:6432", "postgres:5432"
        ).replace(
            "akarai:akarai@", "postgres:postgres@"
        )
        _pg_engine = create_async_engine(url, echo=False)
    return async_sessionmaker(_pg_engine, class_=AsyncSession, expire_on_commit=False)


def _appuser_factory():
    global _app_engine
    if _app_engine is None:
        url = settings.pgbouncer_database_url.replace(
            "pgbouncer:6432", "postgres:5432"
        )
        _app_engine = create_async_engine(url, echo=False)
    return async_sessionmaker(_app_engine, class_=AsyncSession, expire_on_commit=False)


from app.common.rls import (
    apply_rls_context_to_session,
    clear_rls_context_on_session,
    clear_rls_context_vars,
    set_rls_context_vars,
    get_rls_context_values,
    has_rls_context,
)
from app.common.security import hash_password
from app.users.models import User
from app.agencies.models import AgencyTenant
from app.listings.models import Listing, SavedListing, ComparisonSession
from app.viewings.models import ListingViewingSlot, ScheduledViewing
from app.leads.models import Lead
from app.search.models import SearchLog


@pytest.fixture(autouse=True)
async def _dispose_rls_engines():
    """Dispose custom engines between tests to avoid event-loop conflicts."""
    try:
        yield
    finally:
        global _pg_engine, _app_engine
        if _pg_engine is not None:
            await _pg_engine.dispose()
            _pg_engine = None
        if _app_engine is not None:
            await _app_engine.dispose()
            _app_engine = None


def _superuser_session():
    return _superuser_factory()()


@asynccontextmanager
async def _appuser_session():
    factory = _appuser_factory()
    async with factory() as session:
        yield session


async def _create_tenant(session, name="RLS Tenant"):
    tenant = AgencyTenant(
        id=uuid.uuid4(),
        name=name,
        slug=f"rls-tenant-{uuid.uuid4().hex[:8]}",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(tenant)
    await session.commit()
    return tenant


async def _create_user(session, role_id=None):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        email=f"rls-user-{uid.hex[:8]}@test.com",
        password_hash=hash_password("Test1234!"),
        name="RLS Test User",
        role_id=role_id,
        is_active=True,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(user)
    await session.commit()
    return user


async def _create_listing(session, tenant, user=None, status="active", title="RLS Listing"):
    lid = uuid.uuid4()
    listing = Listing(
        id=lid,
        agency_tenant_id=tenant.id,
        title=title,
        property_type="apartment",
        listing_purpose="sale",
        price=100000,
        currency="USD",
        bedrooms=1,
        bathrooms=1,
        area_size=50.0,
        area_unit="sqm",
        city="Test City",
        status=status,
        created_by_user_id=user.id if user else None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(listing)
    await session.commit()
    return listing


@pytest.mark.anyio
class TestRLSTenantIsolation:

    async def test_tenant_a_cannot_see_tenant_b_inactive_listings(self):
        """Tenant A's RLS context hides inactive listings from tenant B."""
        async with _superuser_session() as admin:
            tenant_a = await _create_tenant(admin, name="Tenant A")
            tenant_b = await _create_tenant(admin, name="Tenant B")
            listing_a = await _create_listing(admin, tenant_a, title="Listing A", status="inactive")
            listing_b = await _create_listing(admin, tenant_b, title="Listing B", status="inactive")

        async with _appuser_session() as session:
            await apply_rls_context_to_session(
                session, tenant_id=tenant_a.id, role="agency_admin",
            )
            result = await session.execute(
                select(Listing).where(Listing.id.in_([listing_a.id, listing_b.id]))
            )
            rows = result.scalars().all()
            assert len(rows) == 1, f"Expected 1 listing for tenant A, got {len(rows)}"
            assert rows[0].id == listing_a.id

    async def test_tenant_without_context_sees_only_public(self):
        """Without RLS context, only public (active) listings are visible."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin)
            active_listing = await _create_listing(admin, tenant, status="active", title="Active")
            inactive_listing = await _create_listing(admin, tenant, status="inactive", title="Inactive")

        async with _appuser_session() as session:
            result = await session.execute(
                select(Listing).where(
                    Listing.id.in_([active_listing.id, inactive_listing.id])
                )
            )
            rows = result.scalars().all()
            assert len(rows) == 1, f"Expected 1 public listing, got {len(rows)}"
            assert rows[0].id == active_listing.id
            assert rows[0].status == "active"

    async def test_public_read_sees_active_listings(self):
        """Without tenant context, active listings are visible (public policy)."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin)
            listing = await _create_listing(admin, tenant, status="active")

        async with _appuser_session() as session:
            result = await session.execute(
                select(Listing).where(Listing.id == listing.id)
            )
            row = result.scalar_one_or_none()
            assert row is not None
            assert row.id == listing.id

    async def test_platform_admin_sees_all_tenants(self):
        """Platform admin RLS context bypasses tenant isolation on inactive listings."""
        async with _superuser_session() as admin:
            tenant_a = await _create_tenant(admin, name="Tenant A")
            tenant_b = await _create_tenant(admin, name="Tenant B")
            listing_a = await _create_listing(admin, tenant_a, title="Listing A", status="inactive")
            listing_b = await _create_listing(admin, tenant_b, title="Listing B", status="inactive")

        async with _appuser_session() as session:
            await apply_rls_context_to_session(
                session, role="platform_admin", is_platform_admin=True,
            )
            result = await session.execute(
                select(Listing).where(Listing.id.in_([listing_a.id, listing_b.id]))
            )
            rows = result.scalars().all()
            assert len(rows) == 2, f"Platform admin should see all, got {len(rows)}"


@pytest.mark.anyio
class TestRLSUserIsolation:

    async def test_user_a_cannot_see_user_b_saved_listing(self):
        """User A's RLS context cannot see user B's saved listings."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin)
            user_a = await _create_user(admin)
            user_b = await _create_user(admin)
            listing = await _create_listing(admin, tenant)
            saved_a = SavedListing(id=uuid.uuid4(), user_id=user_a.id, listing_id=listing.id)
            saved_b = SavedListing(id=uuid.uuid4(), user_id=user_b.id, listing_id=listing.id)
            admin.add_all([saved_a, saved_b])
            await admin.commit()

        async with _appuser_session() as session:
            await apply_rls_context_to_session(session, user_id=user_a.id)

            result = await session.execute(
                select(SavedListing).where(
                    SavedListing.id.in_([saved_a.id, saved_b.id])
                )
            )
            rows = result.scalars().all()
            assert len(rows) == 1, f"Expected 1 saved listing, got {len(rows)}"
            assert rows[0].id == saved_a.id

    async def test_user_b_cannot_see_user_a_comparison_session(self):
        """User B's RLS context cannot see user A's comparison sessions."""
        async with _superuser_session() as admin:
            user_a = await _create_user(admin)
            user_b = await _create_user(admin)
            session_a = ComparisonSession(
                id=uuid.uuid4(), user_id=user_a.id, name="A's Comparison",
            )
            session_b = ComparisonSession(
                id=uuid.uuid4(), user_id=user_b.id, name="B's Comparison",
            )
            admin.add_all([session_a, session_b])
            await admin.commit()

        async with _appuser_session() as session:
            await apply_rls_context_to_session(session, user_id=user_a.id)

            result = await session.execute(
                select(ComparisonSession).where(
                    ComparisonSession.id.in_([session_a.id, session_b.id])
                )
            )
            rows = result.scalars().all()
            assert len(rows) == 1, f"Expected 1 comparison session, got {len(rows)}"
            assert rows[0].id == session_a.id

    async def test_no_context_cannot_see_any_saved_listing(self):
        """Without RLS context, user-owned tables return empty results."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin)
            user = await _create_user(admin)
            listing = await _create_listing(admin, tenant)
            saved = SavedListing(id=uuid.uuid4(), user_id=user.id, listing_id=listing.id)
            admin.add(saved)
            await admin.commit()

        async with _appuser_session() as session:
            result = await session.execute(
                select(SavedListing).where(SavedListing.id == saved.id)
            )
            row = result.scalar_one_or_none()
            assert row is None, f"Expected None without context, got {row}"


@pytest.mark.anyio
class TestRLSMixedIsolation:

    async def test_tenant_context_can_see_tenant_viewings(self):
        """Tenant RLS context sees viewings belonging to that tenant."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin)
            user = await _create_user(admin)
            listing = await _create_listing(admin, tenant)

            slot = ListingViewingSlot(
                id=uuid.uuid4(),
                listing_id=listing.id,
                agency_tenant_id=tenant.id,
                starts_at=datetime.now(timezone.utc),
                ends_at=datetime.now(timezone.utc),
                capacity=5,
                status="active",
            )
            viewing = ScheduledViewing(
                id=uuid.uuid4(),
                agency_tenant_id=tenant.id,
                listing_id=listing.id,
                viewing_slot_id=slot.id,
                user_id=user.id,
                scheduled_start_at=datetime.now(timezone.utc),
                scheduled_end_at=datetime.now(timezone.utc),
            )
            admin.add_all([slot, viewing])
            await admin.commit()

        async with _appuser_session() as session:
            await apply_rls_context_to_session(session, tenant_id=tenant.id, role="agency_admin")

            result = await session.execute(
                select(ScheduledViewing).where(ScheduledViewing.id == viewing.id)
            )
            row = result.scalar_one_or_none()
            assert row is not None
            assert row.id == viewing.id

    async def test_user_context_can_see_own_viewings(self):
        """User RLS context sees their own viewings via user_id column."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin)
            user = await _create_user(admin)
            listing = await _create_listing(admin, tenant)

            slot = ListingViewingSlot(
                id=uuid.uuid4(), listing_id=listing.id,
                agency_tenant_id=tenant.id,
                starts_at=datetime.now(timezone.utc),
                ends_at=datetime.now(timezone.utc),
                capacity=5, status="active",
            )
            viewing = ScheduledViewing(
                id=uuid.uuid4(), agency_tenant_id=tenant.id,
                listing_id=listing.id, viewing_slot_id=slot.id,
                user_id=user.id,
                scheduled_start_at=datetime.now(timezone.utc),
                scheduled_end_at=datetime.now(timezone.utc),
            )
            admin.add_all([slot, viewing])
            await admin.commit()

        async with _appuser_session() as session:
            await apply_rls_context_to_session(session, user_id=user.id)

            result = await session.execute(
                select(ScheduledViewing).where(ScheduledViewing.id == viewing.id)
            )
            row = result.scalar_one_or_none()
            assert row is not None
            assert row.id == viewing.id


@pytest.mark.anyio
class TestRLSSearchLogs:

    async def test_public_insert_search_log(self):
        """Even non-superuser can insert search logs (public policy)."""
        async with _appuser_session() as session:
            log = SearchLog(
                id=uuid.uuid4(),
                filters={"location": "Test"},
                result_count=5,
            )
            session.add(log)
            await session.commit()
            assert log.id is not None

    async def test_user_sees_own_search_logs(self):
        """User RLS context sees only their own search logs."""
        async with _superuser_session() as admin:
            user_a = await _create_user(admin)
            user_b = await _create_user(admin)
            log_a = SearchLog(id=uuid.uuid4(), user_id=user_a.id, result_count=5)
            log_b = SearchLog(id=uuid.uuid4(), user_id=user_b.id, result_count=3)
            admin.add_all([log_a, log_b])
            await admin.commit()

        async with _appuser_session() as session:
            await apply_rls_context_to_session(session, user_id=user_a.id)

            result = await session.execute(
                select(SearchLog).where(
                    SearchLog.id.in_([log_a.id, log_b.id])
                )
            )
            rows = result.scalars().all()
            assert len(rows) == 1, f"Expected 1 search log, got {len(rows)}"
            assert rows[0].id == log_a.id


@pytest.mark.anyio
class TestRLSContextHelpers:

    async def test_set_and_clear_context(self):
        tid = uuid.uuid4()
        uid = uuid.uuid4()

        set_rls_context_vars(
            tenant_id=tid, user_id=uid, role="agency_admin", is_platform_admin=False,
        )
        ctx = get_rls_context_values()
        assert ctx["tenant_id"] == str(tid)
        assert ctx["user_id"] == str(uid)
        assert ctx["role"] == "agency_admin"
        assert ctx["is_platform_admin"] is False
        assert has_rls_context() is True

        clear_rls_context_vars()
        ctx = get_rls_context_values()
        assert ctx["tenant_id"] is None
        assert ctx["user_id"] is None
        assert has_rls_context() is False

    async def test_apply_context_to_session(self):
        async with _appuser_session() as session:
            tid = uuid.uuid4()
            uid = uuid.uuid4()

            await apply_rls_context_to_session(
                session, tenant_id=tid, user_id=uid, role="user", is_platform_admin=True,
            )
            result = await session.execute(text("SELECT current_setting('app.tenant_id', true)"))
            assert result.scalar() == str(tid)
            result = await session.execute(text("SELECT current_setting('app.user_id', true)"))
            assert result.scalar() == str(uid)
            result = await session.execute(text("SELECT current_setting('app.is_platform_admin', true)"))
            assert result.scalar() == "true"

    async def test_clear_context_on_session(self):
        async with _appuser_session() as session:
            await apply_rls_context_to_session(
                session, tenant_id=uuid.uuid4(), user_id=uuid.uuid4(),
            )
            await clear_rls_context_on_session(session)
            result = await session.execute(text("SELECT current_setting('app.tenant_id', true)"))
            assert result.scalar() == ""
            result = await session.execute(text("SELECT current_setting('app.user_id', true)"))
            assert result.scalar() == ""


@pytest.mark.anyio
class TestRLSDirectSQL:
    """Tests using raw SQL to prove RLS enforcement at the database level."""

    async def test_raw_sql_cross_tenant_select_denied(self):
        """Raw SQL SELECT across tenants is denied by RLS."""
        async with _superuser_session() as admin:
            tenant_a = await _create_tenant(admin, name="Tenant A Raw")
            tenant_b = await _create_tenant(admin, name="Tenant B Raw")
            listing_a = await _create_listing(admin, tenant_a, title="Listing A Raw", status="inactive")
            listing_b = await _create_listing(admin, tenant_b, title="Listing B Raw", status="inactive")

        async with _appuser_session() as session:
            await apply_rls_context_to_session(
                session, tenant_id=tenant_a.id, role="agency_admin",
            )
            result = await session.execute(
                text("SELECT id, title FROM listings WHERE id IN (:id_a, :id_b)"),
                {"id_a": str(listing_a.id), "id_b": str(listing_b.id)},
            )
            rows = result.fetchall()
            assert len(rows) == 1, f"Expected 1 row with tenant A context, got {len(rows)}"
            assert str(rows[0][0]) == str(listing_a.id)

    async def test_raw_sql_no_context_select_returns_empty(self):
        """Raw SQL SELECT without context returns empty for tenant tables."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin, name="No Context Tenant")
            listing = await _create_listing(admin, tenant, title="No Context Listing", status="inactive")

        async with _appuser_session() as session:
            result = await session.execute(
                text("SELECT id FROM listings WHERE id = :id"),
                {"id": str(listing.id)},
            )
            rows = result.fetchall()
            assert len(rows) == 0, f"Expected 0 rows without context, got {len(rows)}"

    async def test_raw_sql_cross_tenant_update_denied(self):
        """Raw SQL UPDATE across tenants affects 0 rows."""
        async with _superuser_session() as admin:
            tenant_a = await _create_tenant(admin, name="Tenant A Update")
            tenant_b = await _create_tenant(admin, name="Tenant B Update")
            listing_b = await _create_listing(admin, tenant_b, title="Listing B Update", status="inactive")

        async with _appuser_session() as session:
            await apply_rls_context_to_session(
                session, tenant_id=tenant_a.id, role="agency_admin",
            )
            result = await session.execute(
                text("UPDATE listings SET title = :title WHERE id = :id"),
                {"title": "Hacked Title", "id": str(listing_b.id)},
            )
            assert result.rowcount == 0, f"Expected 0 rows updated, got {result.rowcount}"

    async def test_raw_sql_cross_tenant_delete_denied(self):
        """Raw SQL DELETE across tenants affects 0 rows."""
        async with _superuser_session() as admin:
            tenant_a = await _create_tenant(admin, name="Tenant A Delete")
            tenant_b = await _create_tenant(admin, name="Tenant B Delete")
            listing_b = await _create_listing(admin, tenant_b, title="Listing B Delete", status="inactive")

        async with _appuser_session() as session:
            await apply_rls_context_to_session(
                session, tenant_id=tenant_a.id, role="agency_admin",
            )
            result = await session.execute(
                text("DELETE FROM listings WHERE id = :id"),
                {"id": str(listing_b.id)},
            )
            assert result.rowcount == 0, f"Expected 0 rows deleted, got {result.rowcount}"

    async def test_raw_sql_cross_user_select_denied(self):
        """Raw SQL SELECT across users is denied by RLS for user-owned tables."""
        async with _superuser_session() as admin:
            tenant = await _create_tenant(admin, name="User SQL Tenant")
            user_a = await _create_user(admin)
            user_b = await _create_user(admin)
            listing = await _create_listing(admin, tenant)
            saved_a = SavedListing(id=uuid.uuid4(), user_id=user_a.id, listing_id=listing.id)
            saved_b = SavedListing(id=uuid.uuid4(), user_id=user_b.id, listing_id=listing.id)
            admin.add_all([saved_a, saved_b])
            await admin.commit()

        async with _appuser_session() as session:
            await apply_rls_context_to_session(session, user_id=user_a.id)
            result = await session.execute(
                text("SELECT id, user_id FROM saved_listings WHERE id IN (:id_a, :id_b)"),
                {"id_a": str(saved_a.id), "id_b": str(saved_b.id)},
            )
            rows = result.fetchall()
            assert len(rows) == 1, f"Expected 1 row with user A context, got {len(rows)}"
            assert str(rows[0][1]) == str(user_a.id)

    async def test_raw_sql_platform_admin_sees_all(self):
        """Raw SQL with platform_admin context sees all tenants."""
        async with _superuser_session() as admin:
            tenant_a = await _create_tenant(admin, name="Platform A")
            tenant_b = await _create_tenant(admin, name="Platform B")
            listing_a = await _create_listing(admin, tenant_a, title="Platform A Listing", status="inactive")
            listing_b = await _create_listing(admin, tenant_b, title="Platform B Listing", status="inactive")

        async with _appuser_session() as session:
            await apply_rls_context_to_session(
                session, role="platform_admin", is_platform_admin=True,
            )
            result = await session.execute(
                text("SELECT id FROM listings WHERE id IN (:id_a, :id_b)"),
                {"id_a": str(listing_a.id), "id_b": str(listing_b.id)},
            )
            rows = result.fetchall()
            assert len(rows) == 2, f"Expected 2 rows with platform_admin context, got {len(rows)}"
