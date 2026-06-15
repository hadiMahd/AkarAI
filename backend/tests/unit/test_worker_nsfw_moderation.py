"""Unit tests for worker NSFW moderation handler."""

import os
from unittest.mock import patch, MagicMock

import pytest


class TestNSFWModerationHandler:
    """Test NSFW moderation fail-closed behavior."""

    @pytest.mark.anyio
    async def test_moderation_uses_explicit_token(self):
        """Test that moderation passes HF token explicitly to InferenceClient."""
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            from workers.handlers.listing_media import _run_nsfw_moderation
            from app.common.config import Settings, configure_secrets

            s = Settings(_env_file=None)
            s.hf_token = "hf-test-token-xyz"
            configure_secrets(target=s)

            with patch("huggingface_hub.InferenceClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.image_classification.return_value = [
                    {"label": "safe", "score": 0.95},
                    {"label": "nsfw", "score": 0.05},
                ]

                with patch("app.common.config.settings", s):
                    await _run_nsfw_moderation(b"\x00" * 100, content_type="image/png")

                mock_client_class.assert_called_once_with(api_key="hf-test-token-xyz")
                image_arg = mock_client.image_classification.call_args.args[0]
                assert isinstance(image_arg, str)
                assert image_arg.endswith(".png")

    @pytest.mark.anyio
    async def test_moderation_missing_token_fail_closed(self):
        """Test that missing HF token causes fail-closed moderation."""
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            from workers.handlers.listing_media import _run_nsfw_moderation
            from app.common.config import Settings, configure_secrets

            s = Settings(_env_file=None)
            s.hf_token = ""
            configure_secrets(target=s)

            with patch("huggingface_hub.InferenceClient") as mock_client_class:
                with patch("app.common.config.settings", s):
                    result = await _run_nsfw_moderation(b"\x00" * 100)

                # Should reject without even calling InferenceClient
                mock_client_class.assert_not_called()
                assert result["rejected"] is True
                assert result["score"] == 1.0
                assert result["label"] == "moderation_failed"

    @pytest.mark.anyio
    async def test_moderation_service_error_fail_closed(self):
        """Test that service errors cause fail-closed moderation."""
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            from workers.handlers.listing_media import _run_nsfw_moderation
            from app.common.config import Settings, configure_secrets

            s = Settings(_env_file=None)
            s.hf_token = "hf-valid-token"
            configure_secrets(target=s)

            with patch("huggingface_hub.InferenceClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.image_classification.side_effect = Exception("Service unavailable")

                with patch("app.common.config.settings", s):
                    result = await _run_nsfw_moderation(b"\x00" * 100)

                assert result["rejected"] is True
                assert result["score"] == 1.0
                assert result["label"] == "moderation_failed"

    @pytest.mark.anyio
    async def test_moderation_auth_error_fail_closed(self):
        """Test that auth errors (401) cause fail-closed moderation."""
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            from workers.handlers.listing_media import _run_nsfw_moderation
            from app.common.config import Settings, configure_secrets

            s = Settings(_env_file=None)
            s.hf_token = "hf-invalid-token"
            configure_secrets(target=s)

            with patch("huggingface_hub.InferenceClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.image_classification.side_effect = Exception("401 Unauthorized")

                with patch("app.common.config.settings", s):
                    result = await _run_nsfw_moderation(b"\x00" * 100)

                assert result["rejected"] is True
                assert result["score"] == 1.0
                assert result["label"] == "moderation_failed"

    @pytest.mark.anyio
    async def test_moderation_safe_image_passes(self):
        """Test that safe images pass moderation when token is valid."""
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            from workers.handlers.listing_media import _run_nsfw_moderation
            from app.common.config import Settings, configure_secrets

            s = Settings(_env_file=None)
            s.hf_token = "hf-valid-token"
            s.media_nsfw_threshold = 0.75
            configure_secrets(target=s)

            with patch("huggingface_hub.InferenceClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.image_classification.return_value = [
                    {"label": "safe", "score": 0.95},
                    {"label": "nsfw", "score": 0.05},
                ]

                with patch("app.common.config.settings", s):
                    result = await _run_nsfw_moderation(b"\x00" * 100)

                assert result["rejected"] is False
                assert result["score"] == 0.05
                assert result["label"] == "safe"

    @pytest.mark.anyio
    async def test_moderation_nsfw_image_rejected(self):
        """Test that NSFW images are rejected."""
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            from workers.handlers.listing_media import _run_nsfw_moderation
            from app.common.config import Settings, configure_secrets

            s = Settings(_env_file=None)
            s.hf_token = "hf-valid-token"
            s.media_nsfw_threshold = 0.75
            configure_secrets(target=s)

            with patch("huggingface_hub.InferenceClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.image_classification.return_value = [
                    {"label": "safe", "score": 0.10},
                    {"label": "nsfw", "score": 0.90},
                ]

                with patch("app.common.config.settings", s):
                    result = await _run_nsfw_moderation(b"\x00" * 100)

                assert result["rejected"] is True
                assert result["score"] == 0.90
                assert result["label"] == "nsfw"
