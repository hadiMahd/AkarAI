import asyncio
import os
import socket
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

os.environ["APP_ENV"] = "testing"

import app.common.database as _db_module
from app.common.rls import apply_rls_context_to_session

# ── Test engine: NullPool prevents asyncpg connections from being bound to a
# specific event loop.  Anyio and pytest-asyncio create separate loop instances;
# without NullPool, a connection acquired on loop-A fails with
# "Future attached to a different loop" when the next test runs on loop-B.
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def require_test_database() -> None:
    host = _db_module.engine.url.host
    port = _db_module.engine.url.port or 5432
    try:
        socket.getaddrinfo(host, port)
    except OSError:
        pytest.skip(f"test database host {host}:{port} is not reachable")


_test_engine = create_async_engine(
    _db_module.engine.url,
    poolclass=NullPool,
    echo=False,
)
_db_module.engine = _test_engine
_test_base_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
_db_module.async_session_factory = _test_base_factory

_orig_factory = _test_base_factory


class _TestAsyncSession:
    def __init__(self, session):
        self._session = session
        self._wrapped = False

    async def __aenter__(self):
        s = await self._session.__aenter__()
        if not self._wrapped:
            _orig_commit = s.commit

            async def _commit():
                if s.in_transaction() and not s.is_active:
                    await s.rollback()
                await _orig_commit()
                if not s.in_transaction():
                    await s.begin()
                await apply_rls_context_to_session(
                    s, role="platform_admin", is_platform_admin=True,
                )

            s.commit = _commit
            self._wrapped = True
        # Ensure a transaction is active so set_config(..., true) persists
        if not s.in_transaction():
            await s.begin()
        await apply_rls_context_to_session(
            s, role="platform_admin", is_platform_admin=True,
        )
        return s

    async def __aexit__(self, *args):
        return await self._session.__aexit__(*args)

    def __getattr__(self, name):
        return getattr(self._session, name)


class _TestAsyncSessionFactory:
    def __call__(self, **kwargs):
        return _TestAsyncSession(_orig_factory(**kwargs))


_db_module.async_session_factory = _TestAsyncSessionFactory()

from app.auth.models import Role, Permission, RolePermission
from app.users.models import User
from app.agencies.models import AgencyTenant, AgencyEmployeeMembership
from app.listings.models import Listing
from app.leads.models import Lead, ReviewedLeadRecord
from app.viewings.models import ListingViewingSlot, ScheduledViewing, ScheduledViewingStatusHistory
from app.notifications.models import Notification
from app.search.models import SearchLog
from app.common.events import DomainEventLog, OutboxEvent, InboxEvent
from app.rag.models import RagDocument, RagPage, RagChunk, RagRetrievalLog


@pytest.fixture(scope="session", autouse=True)
async def cleanup_test_infra():
    from app.common.redis import close_redis, redis_scan_delete

    await redis_scan_delete("ratelimit:*")
    yield
    await redis_scan_delete("ratelimit:*")
    await close_redis()
    await _test_engine.dispose()


@pytest.fixture(autouse=True)
async def clear_rate_limits():
    from app.common.redis import redis_scan_delete
    count = await redis_scan_delete("ratelimit:*")
    print(f"[CLEAR_RATE_LIMITS] Cleared {count} keys", flush=True)
    yield
    await redis_scan_delete("ratelimit:*")


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
    from app.common.database import async_session_factory

    require_test_database()
    async with async_session_factory() as session:
        _orig_commit = session.commit

        async def _commit():
            if session.in_transaction() and not session.is_active:
                await session.rollback()
            await _orig_commit()
            if not session.in_transaction():
                await session.begin()
            await apply_rls_context_to_session(
                session, role="platform_admin", is_platform_admin=True,
            )

        session.commit = _commit
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def test_user(db_session):
    from sqlalchemy import text
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
async def agency_admin_user(db_session, test_tenant):
    from sqlalchemy import text
    from app.common.security import hash_password
    from app.users.models import User
    from app.agencies.models import AgencyEmployeeMembership

    uid = uuid.uuid4()
    email = f"agency-admin-{uid.hex[:8]}@example.com"
    password = "TestPass123!"
    pw_hash = hash_password(password)

    role_result = await db_session.execute(
        text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1")
    )
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

    membership = AgencyEmployeeMembership(
        id=uuid.uuid4(),
        agency_tenant_id=test_tenant.id,
        user_id=user.id,
        role_id=role_id,
        status="active",
        display_name="Agency Admin Test",
        work_email=email,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()

    yield user, password

    await db_session.delete(membership)
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def support_user(db_session, test_tenant):
    from sqlalchemy import text
    from app.common.security import hash_password
    from app.users.models import User
    from app.agencies.models import AgencyEmployeeMembership

    uid = uuid.uuid4()
    email = f"support-{uid.hex[:8]}@example.com"
    password = "TestPass123!"
    pw_hash = hash_password(password)

    role_result = await db_session.execute(
        text("SELECT id FROM roles WHERE slug = 'support_employee' LIMIT 1")
    )
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

    membership = AgencyEmployeeMembership(
        id=uuid.uuid4(),
        agency_tenant_id=test_tenant.id,
        user_id=user.id,
        role_id=role_id,
        status="active",
        display_name="Support Employee Test",
        work_email=email,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()

    yield user, password

    await db_session.delete(membership)
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

    await db_session.rollback()
    from sqlalchemy import text
    await db_session.execute(text(f"DELETE FROM listings WHERE id = '{lid}'"))
    await db_session.commit()
