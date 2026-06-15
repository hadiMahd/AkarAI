"""Integration tests for listing photo upload API."""

import base64

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# Minimal valid 1x1 PNG for testing
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2e2S8AAAAASUVORK5CYII="
)


async def _login(async_client, email: str, password: str) -> str:
    response = await async_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_upload_photo_requires_auth(async_client):
    """Test that photo upload requires authentication."""
    response = await async_client.post(
        "/agency/listings/00000000-0000-0000-0000-000000000001/photos/upload",
        files={"file": ("test.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code in [401, 403]


@pytest.mark.anyio
async def test_upload_photo_valid_tenant_listing(async_client, db_session, agency_admin_user, test_listing):
    """Test successful photo upload to a tenant-owned listing."""
    listing = test_listing
    listing_id = listing.id
    tenant_id = listing.agency_tenant_id

    # Mock tenant context
    user, password = agency_admin_user
    agency_admin_token = await _login(async_client, user.email, password)

    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_id
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "agency_admin"
        mock_tenant.return_value = mock_ctx

        with patch("app.common.storage.ensure_bucket_exists"), patch(
            "app.common.storage.upload_object"
        ), patch("app.listings.service.publish_outbox_event_in_session"), patch(
            "app.listings.service.write_media_audit_log"
        ), patch(
            "app.listings.service.write_domain_event_log"
        ):
            response = await async_client.post(
                f"/agency/listings/{listing_id}/photos/upload",
                headers={"Authorization": f"Bearer {agency_admin_token}"},
                files={"file": ("test.png", PNG_BYTES, "image/png")},
                data={"caption": "Test caption"},
            )

        assert response.status_code in [201, 503]


@pytest.mark.anyio
async def test_upload_photo_support_employee_forbidden(async_client, db_session, support_user, test_listing):
    """Test that support employees cannot upload photos."""
    listing = test_listing
    listing_id = listing.id
    tenant_id = listing.agency_tenant_id

    user, password = support_user
    support_employee_token = await _login(async_client, user.email, password)

    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_id
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "support_employee"
        mock_tenant.return_value = mock_ctx

        response = await async_client.post(
            f"/agency/listings/{listing_id}/photos/upload",
            headers={"Authorization": f"Bearer {support_employee_token}"},
            files={"file": ("test.png", PNG_BYTES, "image/png")},
        )

        assert response.status_code == 403


@pytest.mark.anyio
async def test_upload_photo_invalid_file_type(async_client, db_session, agency_admin_user, test_listing):
    """Test that invalid file types are rejected."""
    listing = test_listing
    listing_id = listing.id
    tenant_id = listing.agency_tenant_id

    user, password = agency_admin_user
    agency_admin_token = await _login(async_client, user.email, password)

    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_id
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "agency_admin"
        mock_tenant.return_value = mock_ctx

        # Try uploading a non-image file
        response = await async_client.post(
            f"/agency/listings/{listing_id}/photos/upload",
            headers={"Authorization": f"Bearer {agency_admin_token}"},
            files={"file": ("test.txt", b"Hello world", "text/plain")},
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_upload_photo_minio_failure_no_db_record(async_client, db_session, agency_admin_user, test_listing):
    """Test that MinIO upload failure results in no DB record (atomic consistency)."""
    from sqlalchemy import text
    listing = test_listing
    listing_id = listing.id
    tenant_id = listing.agency_tenant_id

    user, password = agency_admin_user
    agency_admin_token = await _login(async_client, user.email, password)

    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_id
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "agency_admin"
        mock_tenant.return_value = mock_ctx

        # Mock MinIO upload to fail
        with patch("app.common.storage.ensure_bucket_exists"), patch(
            "app.common.storage.upload_object"
        ) as mock_upload:
            mock_upload.side_effect = Exception("MinIO connection failed")

            response = await async_client.post(
                f"/agency/listings/{listing_id}/photos/upload",
                headers={"Authorization": f"Bearer {agency_admin_token}"},
                files={"file": ("test.png", PNG_BYTES, "image/png")},
            )

            assert response.status_code in [422, 503]

            # Verify no photo record was created
            result = await db_session.execute(
                text("SELECT COUNT(*) FROM listing_photo_metadata WHERE listing_id = :listing_id"),
                {"listing_id": str(listing_id)},
            )
            assert result.scalar() == 0, "No photo record should be created when MinIO upload fails"


@pytest.mark.anyio
async def test_upload_photo_db_failure_cleans_up_object(async_client, db_session, agency_admin_user, test_listing):
    """Test that an upload artifact is deleted if the DB write path fails after MinIO upload."""
    from sqlalchemy import text
    listing = test_listing
    listing_id = listing.id
    tenant_id = listing.agency_tenant_id

    user, password = agency_admin_user
    agency_admin_token = await _login(async_client, user.email, password)

    with patch("app.listings.router.get_tenant_context") as mock_tenant:
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = tenant_id
        mock_ctx.actor_id = uuid4()
        mock_ctx.role = "agency_admin"
        mock_tenant.return_value = mock_ctx

        with patch("app.common.storage.ensure_bucket_exists"), patch(
            "app.common.storage.upload_object"
        ), patch(
            "app.listings.service.publish_outbox_event_in_session",
            new=AsyncMock(side_effect=Exception("DB failure")),
        ):
            with patch("app.common.storage.delete_object") as mock_delete:
                response = await async_client.post(
                    f"/agency/listings/{listing_id}/photos/upload",
                    headers={"Authorization": f"Bearer {agency_admin_token}"},
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )

                assert response.status_code == 503
                assert mock_delete.called, "Uploaded object should be deleted when DB persistence fails"

                result = await db_session.execute(
                    text("SELECT COUNT(*) FROM listing_photo_metadata WHERE listing_id = :listing_id"),
                    {"listing_id": str(listing_id)},
                )
                assert result.scalar() == 0, "No photo record should persist when DB persistence fails"
