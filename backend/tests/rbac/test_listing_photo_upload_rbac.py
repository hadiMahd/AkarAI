"""RBAC tests for listing photo upload."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


# Minimal valid PNG bytes for testing
PNG_HEADER = (
    b"\x89PNG\r\n\x1a\n"
    + b"\x00" * 8
    + b"\x00" * 25
)


@pytest.mark.asyncio
async def test_upload_photo_cross_tenant_rejected(async_client, db_session):
    """Test that cross-tenant photo uploads are rejected."""
    from app.listings.models import Listing

    listing_id = uuid4()
    tenant_a = uuid4()
    tenant_b = uuid4()

    # Create listing in tenant A
    listing = Listing(
        id=listing_id,
        agency_tenant_id=tenant_a,
        title="Tenant A Listing",
        status="active",
    )
    db_session.add(listing)
    await db_session.flush()

    # Try to upload as tenant B
    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_b
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "agency_admin"
        mock_tenant.return_value = mock_ctx

        response = await async_client.post(
            f"/agency/listings/{listing_id}/photos/upload",
            files={"file": ("test.png", PNG_HEADER, "image/png")},
        )

        # Should fail with 404 (listing not found for this tenant)
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_photo_unauthenticated_rejected(async_client, db_session):
    """Test that unauthenticated users cannot upload photos."""
    listing_id = uuid4()

    response = await async_client.post(
        f"/agency/listings/{listing_id}/photos/upload",
        files={"file": ("test.png", PNG_HEADER, "image/png")},
    )

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_upload_photo_support_employee_rejected(async_client, db_session):
    """Test that support employees cannot upload photos."""
    from app.listings.models import Listing

    listing_id = uuid4()
    tenant_id = uuid4()

    listing = Listing(
        id=listing_id,
        agency_tenant_id=tenant_id,
        title="Test Listing",
        status="active",
    )
    db_session.add(listing)
    await db_session.flush()

    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_id
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "support_employee"
        mock_tenant.return_value = mock_ctx

        response = await async_client.post(
            f"/agency/listings/{listing_id}/photos/upload",
            files={"file": ("test.png", PNG_HEADER, "image/png")},
        )

        assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_photo_regular_user_rejected(async_client, db_session):
    """Test that regular users cannot upload photos."""
    from app.listings.models import Listing

    listing_id = uuid4()
    tenant_id = uuid4()

    listing = Listing(
        id=listing_id,
        agency_tenant_id=tenant_id,
        title="Test Listing",
        status="active",
    )
    db_session.add(listing)
    await db_session.flush()

    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_id
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "user"
        mock_tenant.return_value = mock_ctx

        response = await async_client.post(
            f"/agency/listings/{listing_id}/photos/upload",
            files={"file": ("test.png", PNG_HEADER, "image/png")},
        )

        # Regular users should not have access to agency routes
        assert response.status_code in [403, 404]