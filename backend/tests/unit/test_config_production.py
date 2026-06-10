import os
import pytest
from app.common.config import Settings


class TestProductionConfig:
    """Test production-specific configuration hardening."""

    def test_cors_origins_validation_valid_json(self):
        """Valid JSON array should pass validation."""
        settings = Settings(cors_origins='["https://app.example.com", "https://admin.example.com"]')
        assert settings.effective_cors_origins == ["https://app.example.com", "https://admin.example.com"]

    def test_cors_origins_validation_invalid_json(self):
        """Invalid JSON should raise validation error."""
        with pytest.raises(ValueError, match="cors_origins must be valid JSON"):
            Settings(cors_origins="not-json")

    def test_cors_origins_validation_not_array(self):
        """Non-array JSON should raise validation error."""
        with pytest.raises(ValueError, match="cors_origins must be a JSON array"):
            Settings(cors_origins='"single-string"')

    def test_cors_origins_validation_non_string_elements(self):
        """Array with non-string elements should raise validation error."""
        with pytest.raises(ValueError, match="Each CORS origin must be a string"):
            Settings(cors_origins='["https://example.com", 123]')

    def test_production_rejects_wildcard_cors(self):
        """Production should reject wildcard CORS origin."""
        settings = Settings(app_env="production", cors_origins='["https://app.example.com", "*"]')
        with pytest.raises(ValueError, match="Wildcard CORS origin"):
            settings.effective_cors_origins

    def test_production_requires_explicit_cors(self):
        """Production should require explicit CORS origins."""
        settings = Settings(app_env="production", cors_origins="[]")
        with pytest.raises(ValueError, match="cors_origins must be explicitly configured"):
            settings.effective_cors_origins

    def test_development_allows_wildcard_cors(self):
        """Development should allow wildcard for local testing."""
        settings = Settings(app_env="development", cors_origins='["http://localhost:3000", "*"]')
        assert "*" in settings.effective_cors_origins

    def test_production_cookie_secure_true(self):
        """Production should force secure cookies."""
        settings = Settings(app_env="production", auth_cookie_secure=False)
        assert settings.effective_cookie_secure is True

    def test_development_cookie_secure_false(self):
        """Development should respect explicit setting."""
        settings = Settings(app_env="development", auth_cookie_secure=False)
        assert settings.effective_cookie_secure is False

    def test_production_cookie_samesite_strict(self):
        """Production should force strict SameSite."""
        settings = Settings(app_env="production", auth_cookie_samesite="lax")
        assert settings.effective_cookie_samesite == "strict"

    def test_development_cookie_samesite_lax(self):
        """Development should respect explicit setting."""
        settings = Settings(app_env="development", auth_cookie_samesite="lax")
        assert settings.effective_cookie_samesite == "lax"

    def test_production_cors_allow_credentials_explicit_only(self):
        """Production should only allow credentials with explicit origins."""
        settings = Settings(app_env="production", cors_origins='["https://app.example.com"]')
        assert settings.effective_cors_allow_credentials is True

    def test_production_cors_allow_credentials_false_with_wildcard(self):
        """Production should deny credentials if wildcard present."""
        settings = Settings(app_env="production", cors_origins='["https://app.example.com", "*"]')
        with pytest.raises(ValueError, match="Wildcard CORS origin"):
            settings.effective_cors_allow_credentials
        pass

    def test_staging_uses_production_hardening(self):
        """Staging should also use production-like hardening."""
        settings = Settings(app_env="staging", cors_origins='["https://staging.example.com"]')
        assert settings.effective_cookie_secure is True
        assert settings.effective_cookie_samesite == "strict"

    def test_testing_environment_permissive(self):
        """Testing should be permissive for testability."""
        settings = Settings(app_env="testing", auth_cookie_secure=False, auth_cookie_samesite="lax")
        assert settings.effective_cookie_secure is False
        assert settings.effective_cookie_samesite == "lax"


class TestConfigValidation:
    """Test configuration validation edge cases."""

    def test_invalid_app_env(self):
        """Invalid app_env should raise validation error."""
        with pytest.raises(ValueError, match="app_env must be one of"):
            Settings(app_env="invalid")

    def test_invalid_samesite(self):
        """Invalid SameSite value should raise validation error."""
        with pytest.raises(ValueError, match="auth_cookie_samesite must be one of"):
            Settings(auth_cookie_samesite="invalid")

    def test_valid_samesite_values(self):
        """All valid SameSite values should work."""
        for value in ["lax", "strict", "none", "LAX", "STRICT", "NONE"]:
            settings = Settings(auth_cookie_samesite=value)
            assert settings.auth_cookie_samesite == value.lower()