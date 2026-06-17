import os
from unittest.mock import patch, MagicMock

import pytest

from app.common.config import Settings


class TestSettingsLoading:
    def test_defaults(self):
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            s = Settings(_env_file=None)
            assert s.app_env == "testing"
            assert s.project_name == "AkarAI"
            assert s.backend_port == 8000
            assert s.jwt_algorithm == "HS256"
            assert s.pagination_default_page_size == 20
            assert s.pagination_max_page_size == 100
            assert s.jwt_access_secret == ""
            assert s.jwt_refresh_secret == ""
            assert s.hf_token == ""

    def test_env_override(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=True):
            s = Settings(_env_file=None)
            assert s.app_env == "staging"
            assert s.project_name == "AkarAI"

    def test_invalid_app_env(self):
        with patch.dict(os.environ, {"APP_ENV": "invalid"}, clear=True):
            with pytest.raises(ValueError, match="app_env must be one of"):
                Settings(_env_file=None)

    def test_provider_placeholders(self):
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            s = Settings(_env_file=None)
            assert s.ai_primary_provider == "azure_openai"
            assert s.ai_fallback_providers == "openrouter"
            assert s.cohere_api_key == "TBD_ASK_USER"
            assert s.email_provider == "resend"

    def test_pagination_bounds(self):
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            s = Settings(_env_file=None)
            assert s.pagination_default_page_size > 0
            assert s.pagination_max_page_size >= s.pagination_default_page_size

    def test_rate_limit_config(self):
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            s = Settings(_env_file=None)
            assert s.rate_limit_default_window_seconds > 0
            assert s.rate_limit_default_max_requests > 0

    def test_configure_secrets_testing(self):
        with patch.dict(os.environ, {"APP_ENV": "testing"}, clear=True):
            s = Settings(_env_file=None)
            assert s.jwt_access_secret == ""
            assert s.jwt_refresh_secret == ""

            from app.common.config import configure_secrets
            configure_secrets(target=s)

            assert s.jwt_access_secret == "test-access-secret-for-unit-tests"
            assert s.jwt_refresh_secret == "test-refresh-secret-for-unit-tests"
            # In testing, HF token should remain empty (optional)
            assert s.hf_token == ""

    def test_configure_secrets_vault_unreachable(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "VAULT_ADDR": "http://no-vault:8200", "VAULT_TOKEN": "root"}, clear=True):
            s = Settings(_env_file=None)
            from app.common.config import configure_secrets
            with pytest.raises(RuntimeError, match="Vault is unreachable"):
                configure_secrets(target=s)

    def test_configure_secrets_loads_hf_and_azure_from_vault(self):
        """Test that configure_secrets loads HF token and Azure config from Vault."""
        with patch.dict(os.environ, {"APP_ENV": "development", "VAULT_ADDR": "http://vault:8200", "VAULT_TOKEN": "root"}, clear=True):
            s = Settings(_env_file=None)

            from app.common.config import configure_secrets

            # Mock hvac client
            with patch("app.common.config.hvac.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.sys.is_initialized.return_value = True
                mock_client.sys.is_sealed.return_value = False

                # Mock JWT secret read
                mock_client.secrets.kv.v2.read_secret_version.side_effect = [
                    # First call: akarai/jwt
                    {"data": {"data": {"access_secret": "jwt-access", "refresh_secret": "jwt-refresh"}}},
                    # Second call: akarai/ai
                    {"data": {"data": {"hf_token": "hf-test-token-123"}}},
                    # Third call: akarai/azure
                    {
                        "data": {
                            "data": {
                                "endpoint": "https://azure.example/openai/v1",
                                "api_key": "azure-key-123",
                                "chat_deployment": "gpt-5-chat",
                                "embedding_deployment": "text-embedding-3-small",
                                "whisper_deployment": "whisper-1",
                                "embedding_model": "text-embedding-3-small",
                            }
                        }
                    },
                    # Fourth call: akarai/openrouter
                    {
                        "data": {
                            "data": {
                                "api_key": "or-test-key",
                                "base_url": "https://openrouter.ai/api/v1",
                                "rerank_model": "test/rerank-model",
                                "content_safety_model": "test/content-safety-model",
                            }
                        }
                    },
                    # Fifth call: akarai/azure_cv
                    {
                        "data": {
                            "data": {
                                "endpoint": "https://vision.example/read/v3.2",
                                "api_key": "vision-key-123",
                            }
                        }
                    },
                    # Sixth call: akarai/lead_model_service
                    {
                        "data": {
                            "data": {
                                "service_url": "http://lead-model-service:8100",
                                "callback_token": "lead-callback-token",
                            }
                        }
                    },
                ]

                configure_secrets(target=s)

                assert s.jwt_access_secret == "jwt-access"
                assert s.jwt_refresh_secret == "jwt-refresh"
                assert s.hf_token == "hf-test-token-123"
                assert s.azure_openai_endpoint == "https://azure.example/openai/v1"
                assert s.azure_openai_api_key == "azure-key-123"
                assert s.azure_openai_chat_deployment == "gpt-5-chat"
                assert s.azure_openai_embedding_deployment == "text-embedding-3-small"
                assert s.azure_whisper_deployment == "whisper-1"
                assert s.azure_openai_embedding_model == "text-embedding-3-small"
                assert s.openrouter_api_key == "or-test-key"
                assert s.openrouter_rerank_model == "test/rerank-model"
                assert s.openrouter_content_safety_model == "test/content-safety-model"
                assert s.azure_cv_endpoint == "https://vision.example/read/v3.2"
                assert s.azure_cv_api_key == "vision-key-123"
                assert s.lead_model_service_url == "http://lead-model-service:8100"
                assert s.lead_model_service_callback_token == "lead-callback-token"

                # Verify all secrets were read
                assert mock_client.secrets.kv.v2.read_secret_version.call_count == 6
                calls = mock_client.secrets.kv.v2.read_secret_version.call_args_list
                assert calls[0].kwargs == {"path": "jwt", "mount_point": "akarai", "raise_on_deleted_version": True}
                assert calls[1].kwargs == {"path": "ai", "mount_point": "akarai", "raise_on_deleted_version": True}
                assert calls[2].kwargs == {"path": "azure", "mount_point": "akarai", "raise_on_deleted_version": True}
                assert calls[3].kwargs == {"path": "openrouter", "mount_point": "akarai", "raise_on_deleted_version": True}
                assert calls[4].kwargs == {"path": "azure_cv", "mount_point": "akarai", "raise_on_deleted_version": True}
                assert calls[5].kwargs == {"path": "lead_model_service", "mount_point": "akarai", "raise_on_deleted_version": True}

    def test_configure_secrets_optional_ai_secrets_missing_from_vault(self):
        """Test that configure_secrets handles missing optional AI secrets gracefully."""
        with patch.dict(os.environ, {"APP_ENV": "development", "VAULT_ADDR": "http://vault:8200", "VAULT_TOKEN": "root"}, clear=True):
            s = Settings(_env_file=None)

            from app.common.config import configure_secrets
            import hvac

            # Mock hvac client
            with patch("app.common.config.hvac.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.sys.is_initialized.return_value = True
                mock_client.sys.is_sealed.return_value = False

                # Mock JWT secret read success, optional AI paths missing
                mock_client.secrets.kv.v2.read_secret_version.side_effect = [
                    # First call: akarai/jwt
                    {"data": {"data": {"access_secret": "jwt-access", "refresh_secret": "jwt-refresh"}}},
                    # Second call: akarai/ai - not found
                    hvac.exceptions.InvalidPath("No secret found"),
                    # Third call: akarai/azure - not found
                    hvac.exceptions.InvalidPath("No secret found"),
                    # Fourth call: akarai/openrouter - not found
                    hvac.exceptions.InvalidPath("No secret found"),
                    # Fifth call: akarai/azure_cv - not found
                    hvac.exceptions.InvalidPath("No secret found"),
                    # Sixth call: akarai/lead_model_service - not found
                    hvac.exceptions.InvalidPath("No secret found"),
                ]

                configure_secrets(target=s)

                assert s.jwt_access_secret == "jwt-access"
                assert s.jwt_refresh_secret == "jwt-refresh"
                assert s.hf_token == ""  # Empty when not configured
                assert s.azure_openai_api_key == ""
                assert s.openrouter_content_safety_model == ""
                assert s.azure_cv_api_key == ""
