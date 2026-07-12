"""Integration tests for listing photo processing lifecycle."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.anyio
async def test_worker_handles_missing_fields_gracefully():
    """Malformed media events are terminal and do not retry forever."""
    from workers.handlers.listing_media import NonRetryableEventError, handle_listing_image_uploaded

    mock_conn = MagicMock()
    mock_conn.execute = MagicMock(return_value=None)

    with pytest.raises(NonRetryableEventError):
        await handle_listing_image_uploaded(mock_conn, {}, "event-1")


@pytest.mark.anyio
async def test_worker_propagates_moderation_failure_for_retry():
    """A provider outage must not be persisted as a rejected image."""
    from app.common.config import settings

    from workers.handlers.listing_media import _run_nsfw_moderation

    with (
        patch.object(settings, "hf_token", "hf-test-token"),
        patch("huggingface_hub.InferenceClient") as mock_client,
    ):
        mock_client.side_effect = Exception("Service unavailable")

        with pytest.raises(Exception, match="Service unavailable"):
            await _run_nsfw_moderation(b"\x00" * 100)
