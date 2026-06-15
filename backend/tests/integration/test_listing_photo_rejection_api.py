"""Integration tests for listing photo rejection (NSFW and invalid uploads)."""

import base64
import pytest
from unittest.mock import AsyncMock, patch


# Minimal valid 1x1 PNG bytes for testing
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2e2S8AAAAASUVORK5CYII="
)


async def _login(async_client, email: str, password: str) -> str:
    response = await async_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_upload_rejects_invalid_file_type(async_client, agency_admin_user, test_listing):
    """Test that invalid file types are rejected at upload."""
    user, password = agency_admin_user
    token = await _login(async_client, user.email, password)

    response = await async_client.post(
        f"/agency/listings/{test_listing.id}/photos/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", b"This is not an image", "text/plain")},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_upload_rejects_oversized_file(async_client, agency_admin_user, test_listing):
    """Test that oversized files are rejected."""
    user, password = agency_admin_user
    token = await _login(async_client, user.email, password)

    large_data = b"\x00" * (11 * 1024 * 1024)
    response = await async_client.post(
        f"/agency/listings/{test_listing.id}/photos/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("large.png", large_data, "image/png")},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_upload_accepts_valid_image(async_client, agency_admin_user, test_listing):
    """Test that valid images are accepted."""
    user, password = agency_admin_user
    token = await _login(async_client, user.email, password)

    with patch("app.common.storage.ensure_bucket_exists"), patch(
        "app.common.storage.upload_object"
    ), patch(
        "app.listings.service.publish_outbox_event_in_session", new=AsyncMock()
    ), patch(
        "app.listings.service.write_media_audit_log", new=AsyncMock()
    ), patch(
        "app.listings.service.write_domain_event_log", new=AsyncMock()
    ):
        response = await async_client.post(
            f"/agency/listings/{test_listing.id}/photos/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.png", PNG_BYTES, "image/png")},
        )

    assert response.status_code in [201, 503]


@pytest.mark.anyio
async def test_preflight_marks_safe_image_as_uploadable(async_client, agency_admin_user):
    user, password = agency_admin_user
    token = await _login(async_client, user.email, password)

    with patch(
        "app.listings.service.run_nsfw_moderation",
        new=AsyncMock(return_value={"rejected": False, "score": 0.03, "label": "safe"}),
    ):
        response = await async_client.post(
            "/agency/listings/photos/validate",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.png", PNG_BYTES, "image/png")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["safe"] is True
    assert body["message"] == "Image is safe to upload."
    assert body["moderation_label"] == "safe"


@pytest.mark.anyio
async def test_preflight_rejects_nsfw_image(async_client, agency_admin_user):
    user, password = agency_admin_user
    token = await _login(async_client, user.email, password)

    with patch(
        "app.listings.service.run_nsfw_moderation",
        new=AsyncMock(return_value={"rejected": True, "score": 0.98, "label": "nsfw"}),
    ):
        response = await async_client.post(
            "/agency/listings/photos/validate",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.png", PNG_BYTES, "image/png")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["safe"] is False
    assert body["rejection_reason"] == "nsfw"
    assert "unsafe" in body["message"].lower()
