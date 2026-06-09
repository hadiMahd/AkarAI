import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

os.environ["APP_ENV"] = "testing"


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

