import os
from unittest.mock import patch

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

    def test_configure_secrets_vault_unreachable(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "VAULT_ADDR": "http://no-vault:8200", "VAULT_TOKEN": "root"}, clear=True):
            s = Settings(_env_file=None)
            from app.common.config import configure_secrets
            with pytest.raises(RuntimeError, match="Vault is unreachable"):
                configure_secrets(target=s)
