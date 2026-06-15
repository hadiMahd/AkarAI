"""RBAC tests for listing photo upload."""

import base64
import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime, timezone


# Minimal valid 1x1 PNG for testing
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2e2S8AAAAASUVORK5CYII="
)


async def _login(async_client, email: str, password: str) -> str:
    resp = await async_client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_tenant_admin(db_session, slug_prefix: str):
    from sqlalchemy import text
    from app.agencies.models import AgencyEmployeeMembership, AgencyTenant
    from app.common.security import hash_password
    from app.users.models import User

    now = datetime.now(timezone.utc)
    tenant = AgencyTenant(
        id=uuid4(),
        name=f"{slug_prefix}-tenant",
        slug=f"{slug_prefix}-{uuid4().hex[:8]}",
        status="active",
        created_at=now,
        updated_at=now,
    )
    user = User(
        id=uuid4(),
        email=f"{slug_prefix}-user-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass123!"),
        name=f"{slug_prefix} User",
        role_id=None,
        is_active=True,
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(user)
    await db_session.flush()

    role_result = await db_session.execute(
        text("SELECT id FROM roles WHERE slug = :slug LIMIT 1"),
        {"slug": "agency_admin"},
    )
    role_id = role_result.scalar_one()
    user.role_id = role_id

    membership = AgencyEmployeeMembership(
        id=uuid4(),
        agency_tenant_id=tenant.id,
        user_id=user.id,
        role_id=role_id,
        status="active",
        display_name=f"{slug_prefix} Display",
        work_email=user.email,
        created_at=now,
        updated_at=now,
    )
    db_session.add(membership)
    await db_session.commit()
    return tenant, user, membership, "TestPass123!"


@pytest.mark.anyio
async def test_upload_photo_unauthenticated_rejected(async_client, db_session):
    """Test that unauthenticated users cannot upload photos."""
    resp = await async_client.post(
        f"/agency/listings/{uuid4()}/photos/upload",
        files={"file": ("test.png", PNG_BYTES, "image/png")},
    )
    assert resp.status_code in [401, 403]


@pytest.mark.anyio
async def test_upload_photo_cross_tenant_rejected(async_client, db_session):
    """Test that cross-tenant photo uploads are rejected."""
    from app.listings.models import Listing

    now = datetime.now(timezone.utc)
    tenant_a, user_a, _, password_a = await _create_tenant_admin(db_session, "cross-a")
    tenant_b, user_b, _, password_b = await _create_tenant_admin(db_session, "cross-b")

    listing = Listing(
        id=uuid4(),
        agency_tenant_id=tenant_a.id,
        title="Tenant A Listing",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(listing)
    await db_session.commit()

    token_b = await _login(async_client, user_b.email, password_b)
    resp = await async_client.post(
        f"/agency/listings/{listing.id}/photos/upload",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("test.png", PNG_BYTES, "image/png")},
    )
    assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}: {resp.text[:300]}"


@pytest.mark.anyio
async def test_upload_photo_support_employee_rejected(async_client, db_session):
    """Test that support employees cannot upload photos."""
    from app.auth.dependencies import get_tenant_context
    from app.listings.models import Listing
    from app.main import app

    now = datetime.now(timezone.utc)
    tenant, user_a, _, _ = await _create_tenant_admin(db_session, "support-test")

    listing = Listing(
        id=uuid4(),
        agency_tenant_id=tenant.id,
        title="Test Listing",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(listing)
    await db_session.commit()

    token = await _login(async_client, user_a.email, "TestPass123!")

    mock_ctx = MagicMock()
    mock_ctx.tenant_id = tenant.id
    mock_ctx.actor_id = user_a.id
    mock_ctx.role = "support_employee"
    mock_ctx.permissions = []

    async def override_get_tenant_context():
        return mock_ctx

    app.dependency_overrides[get_tenant_context] = override_get_tenant_context
    try:
        resp = await async_client.post(
            f"/agency/listings/{listing.id}/photos/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.png", PNG_BYTES, "image/png")},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text[:300]}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_upload_photo_regular_user_rejected(async_client, db_session):
    """Test that regular users cannot upload photos."""
    from app.listings.models import Listing

    now = datetime.now(timezone.utc)
    tenant, user_a, _, password_a = await _create_tenant_admin(db_session, "reguser-test")

    listing = Listing(
        id=uuid4(),
        agency_tenant_id=tenant.id,
        title="Test Listing",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(listing)
    await db_session.commit()

    user_token = await _login(async_client, "user@akarai.test", "Test1234!")
    resp = await async_client.post(
        f"/agency/listings/{listing.id}/photos/upload",
        headers={"Authorization": f"Bearer {user_token}"},
        files={"file": ("test.png", PNG_BYTES, "image/png")},
    )
    assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}: {resp.text[:300]}"
