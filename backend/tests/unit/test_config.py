import os
from unittest.mock import patch

import pytest

from app.common.config import Settings


class TestSettingsLoading:
    def test_defaults(self):
        s = Settings()
        assert s.app_env == "development"
        assert s.project_name == "AkarAI"
        assert s.backend_port == 8000
        assert s.jwt_algorithm == "HS256"
        assert s.pagination_default_page_size == 20
        assert s.pagination_max_page_size == 100

    def test_env_override(self):
        with patch.dict(os.environ, {"APP_ENV": "staging", "PROJECT_NAME": "TestApp"}, clear=True):
            s = Settings(_env_file=None)
            assert s.app_env == "staging"
            assert s.project_name == "TestApp"

    def test_invalid_app_env(self):
        with patch.dict(os.environ, {"APP_ENV": "invalid"}, clear=True):
            with pytest.raises(ValueError, match="app_env must be one of"):
                Settings(_env_file=None)

    def test_provider_placeholders(self):
        s = Settings()
        assert s.ai_primary_provider == "TBD_ASK_USER"
        assert s.ai_fallback_providers == "TBD_ASK_USER"
        assert s.cohere_api_key == "TBD_ASK_USER"
        assert s.email_provider == "TBD_ASK_USER"
        assert s.jwt_access_secret == "TBD_ASK_USER"
        assert s.jwt_refresh_secret == "TBD_ASK_USER"

    def test_pagination_bounds(self):
        s = Settings()
        assert s.pagination_default_page_size > 0
        assert s.pagination_max_page_size >= s.pagination_default_page_size

    def test_rate_limit_config(self):
        s = Settings()
        assert s.rate_limit_default_window_seconds > 0
        assert s.rate_limit_default_max_requests > 0
