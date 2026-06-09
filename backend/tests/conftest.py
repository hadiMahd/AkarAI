import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

os.environ["APP_ENV"] = "testing"

from app.auth.models import Role, Permission, RolePermission
from app.users.models import User
from app.agencies.models import AgencyTenant, AgencyEmployeeMembership
from app.listings.models import Listing
from app.leads.models import Lead, ReviewedLeadRecord
from app.viewings.models import ListingViewingSlot, ScheduledViewing, ScheduledViewingStatusHistory
from app.notifications.models import Notification
from app.search.models import SearchLog
from app.common.events import DomainEventLog, OutboxEvent, InboxEvent


@pytest.fixture(autouse=True)
async def clear_rate_limits():
    from app.common.redis import redis_scan_delete
    await redis_scan_delete("ratelimit:*")
    yield
    await redis_scan_delete("ratelimit:*")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session() -> AsyncGenerator:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.common.database import async_session_factory

    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def test_user(db_session):
    from sqlalchemy import select as sa_select, text
    from app.common.security import hash_password
    from app.users.models import User

    uid = uuid.uuid4()
    email = f"test-{uid.hex[:8]}@example.com"
    password = "TestPass123!"
    pw_hash = hash_password(password)

    role_result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'user' LIMIT 1"))
    role_row = role_result.fetchone()
    role_id = role_row[0] if role_row else None

    user = User(
        id=uid,
        email=email,
        password_hash=pw_hash,
        name="Test User",
        role_id=role_id,
        is_active=True,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()

    yield user, password

    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def agency_admin_user(db_session):
    from sqlalchemy import text
    from app.common.security import hash_password
    from app.users.models import User

    uid = uuid.uuid4()
    email = f"agency-admin-{uid.hex[:8]}@example.com"
    password = "TestPass123!"
    pw_hash = hash_password(password)

    role_result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1"))
    role_row = role_result.fetchone()
    role_id = role_row[0] if role_row else None

    user = User(
        id=uid,
        email=email,
        password_hash=pw_hash,
        name="Agency Admin Test",
        role_id=role_id,
        is_active=True,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()

    yield user, password

    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def support_user(db_session):
    from sqlalchemy import text
    from app.common.security import hash_password
    from app.users.models import User

    uid = uuid.uuid4()
    email = f"support-{uid.hex[:8]}@example.com"
    password = "TestPass123!"
    pw_hash = hash_password(password)

    role_result = await db_session.execute(text("SELECT id FROM roles WHERE slug = 'support_employee' LIMIT 1"))
    role_row = role_result.fetchone()
    role_id = role_row[0] if role_row else None

    user = User(
        id=uid,
        email=email,
        password_hash=pw_hash,
        name="Support Employee Test",
        role_id=role_id,
        is_active=True,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()

    yield user, password

    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def test_tenant(db_session):
    from sqlalchemy import text
    from app.agencies.models import AgencyTenant

    tid = uuid.uuid4()
    slug = f"test-tenant-{tid.hex[:8]}"
    tenant = AgencyTenant(
        id=tid,
        name=f"Test Tenant {tid.hex[:4]}",
        slug=slug,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(tenant)
    await db_session.commit()

    yield tenant

    await db_session.delete(tenant)
    await db_session.commit()


@pytest.fixture
async def test_listing(db_session, test_tenant, agency_admin_user):
    from app.listings.models import Listing

    user, _ = agency_admin_user
    lid = uuid.uuid4()
    listing = Listing(
        id=lid,
        agency_tenant_id=test_tenant.id,
        title="Test Listing",
        description="A test property",
        property_type="apartment",
        listing_purpose="sale",
        price=250000,
        currency="USD",
        bedrooms=2,
        bathrooms=1,
        area_size=85.5,
        area_unit="sqm",
        furnishing="furnished",
        location_text="Test City",
        address="123 Test St",
        city="Test City",
        country="Test Country",
        status="active",
        created_by_user_id=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(listing)
    await db_session.commit()

    yield listing

    from sqlalchemy import text
    await db_session.execute(text(f"DELETE FROM listings WHERE id = '{lid}'"))
    await db_session.commit()

