import pytest
from unittest.mock import patch, MagicMock

import app.common.storage as storage_mod


def _reset_caches():
    """Clear module-level MinIO client caches for test isolation."""
    storage_mod._minio_client = None
    storage_mod._minio_public_client = None


class TestPresignedUrlPublicHost:
    """Verify that presigned_get_url uses the public host for URL generation."""

    def setup_method(self):
        _reset_caches()

    def test_public_client_passes_region_to_skip_head_request(self):
        _reset_caches()
        with (
            patch.object(storage_mod, "settings") as mock_settings,
            patch.object(storage_mod, "Minio") as mock_minio,
        ):
            mock_settings.minio_public_url = "localhost:9000"
            mock_settings.minio_endpoint = "minio:9000"
            mock_settings.minio_access_key = "ak"
            mock_settings.minio_secret_key = "sk"
            mock_settings.minio_secure = False

            storage_mod.get_public_minio()

            assert mock_minio.call_args.kwargs["region"] == "us-east-1"

    def test_public_client_uses_configured_endpoint(self):
        _reset_caches()
        with (
            patch.object(storage_mod, "settings") as mock_settings,
            patch.object(storage_mod, "Minio") as mock_minio,
        ):
            mock_settings.minio_public_url = "localhost:9000"
            mock_settings.minio_endpoint = "minio:9000"
            mock_settings.minio_access_key = "ak"
            mock_settings.minio_secret_key = "sk"
            mock_settings.minio_secure = False

            storage_mod.get_public_minio()

            args = mock_minio.call_args.args
            assert args[0] == "localhost:9000"

    def test_fallback_uses_internal_endpoint(self):
        _reset_caches()
        with (
            patch.object(storage_mod, "settings") as mock_settings,
            patch.object(storage_mod, "Minio") as mock_minio,
        ):
            mock_settings.minio_public_url = ""
            mock_settings.minio_endpoint = "minio:9000"
            mock_settings.minio_access_key = "ak"
            mock_settings.minio_secret_key = "sk"
            mock_settings.minio_secure = False

            storage_mod.get_public_minio()

            args = mock_minio.call_args.args
            assert args[0] == "minio:9000"

    def test_internal_client_uses_internal_endpoint(self):
        _reset_caches()
        with (
            patch.object(storage_mod, "settings") as mock_settings,
            patch.object(storage_mod, "Minio") as mock_minio,
        ):
            mock_settings.minio_endpoint = "minio:9000"
            mock_settings.minio_access_key = "ak"
            mock_settings.minio_secret_key = "sk"
            mock_settings.minio_secure = False

            storage_mod.get_minio()

            args = mock_minio.call_args.args
            assert args[0] == "minio:9000"
            kw = mock_minio.call_args.kwargs
            assert kw.get("region") is None

    def test_public_and_internal_clients_use_different_endpoints(self):
        _reset_caches()
        endpoints = []
        def minio_side_effect(*args, **kwargs):
            endpoints.append(args[0])
            return MagicMock()

        with (
            patch.object(storage_mod, "settings") as mock_settings,
            patch.object(storage_mod, "Minio", side_effect=minio_side_effect),
        ):
            mock_settings.minio_public_url = "localhost:9000"
            mock_settings.minio_endpoint = "minio:9000"
            mock_settings.minio_access_key = "ak"
            mock_settings.minio_secret_key = "sk"
            mock_settings.minio_secure = False

            _reset_caches()
            storage_mod.get_minio()
            storage_mod.get_public_minio()

        assert endpoints == ["minio:9000", "localhost:9000"]
