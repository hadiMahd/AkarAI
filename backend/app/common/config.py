import json
from typing import Optional, List

import hvac
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    app_env: str = "development"
    app_debug: bool = True
    project_name: str = "AkarAI"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Database (PgBouncer runtime)
    database_url: str = "postgresql+asyncpg://akarai:akarai@pgbouncer:6432/akarai"
    pgbouncer_database_url: str = "postgresql+asyncpg://akarai:akarai@pgbouncer:6432/akarai"
    database_sync_url: str = "postgresql+psycopg2://akarai:akarai@pgbouncer:6432/akarai"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_rag: str = "rag-vault"
    minio_bucket_media: str = "property-media"

    # CORS — explicit allowlist; production requires explicit configuration
    cors_origins: str = '["http://localhost:3000","http://localhost:3001","http://localhost:8501"]'
    # In production, cors_origins MUST be set via env var to explicit production domains
    # No wildcard (*) allowed when allow_credentials=True

    # Vault (bootstrap only — secrets at runtime)
    vault_addr: str = "http://vault:8200"
    vault_token: str = "root"

    # JWT (secrets loaded from Vault at startup via configure_secrets())
    jwt_access_secret: str = ""
    jwt_refresh_secret: str = ""
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    jwt_algorithm: str = "HS256"

    # Auth Cookie Settings
    auth_refresh_cookie_name: str = "akarai_refresh"
    auth_refresh_cookie_path: str = "/"
    auth_cookie_secure: bool = False
    # CSRF PROTECTION NOTE:
    # Current CSRF protection relies on SameSite=lax cookie policy for cookie-authenticated endpoints.
    # This is acceptable as long as:
    # 1. Refresh tokens stay in HttpOnly cookies with SameSite=lax or strict
    # 2. The deployment uses the same host/site (frontend and backend on same domain)
    # If you change to SameSite=None (cross-site cookies) or a different deployment shape,
    # you MUST reintroduce explicit CSRF token enforcement (verify_csrf_token dependency)
    # on all cookie-authenticated state-changing endpoints.
    auth_cookie_samesite: str = "lax"
    auth_cookie_domain: Optional[str] = None
    auth_cookie_httponly: bool = True

    # AI Providers
    ai_primary_provider: str = "azure_openai"
    ai_fallback_providers: str = "openrouter"
    cohere_api_key: str = "TBD_ASK_USER"

    # Email Provider
    email_provider: str = "resend"

    # Pagination
    pagination_default_page_size: int = 20
    pagination_max_page_size: int = 100

    # Rate Limiting
    rate_limit_default_window_seconds: int = 60
    rate_limit_default_max_requests: int = 30

    # Request ID
    request_id_header: str = "X-Request-Id"

    # Agency employee onboarding
    agency_employee_initial_password: str = "12345678"

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "testing", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got '{v}'")
        return v

    @field_validator("auth_cookie_samesite")
    @classmethod
    def validate_samesite(cls, v: str) -> str:
        allowed = {"lax", "strict", "none"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"auth_cookie_samesite must be one of {allowed}, got '{v}'")
        return v_lower

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("cors_origins must be a JSON array")
            for origin in parsed:
                if not isinstance(origin, str):
                    raise ValueError("Each CORS origin must be a string")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"cors_origins must be valid JSON array: {e}") from e

    @computed_field
    @property
    def effective_cors_origins(self) -> List[str]:
        origins = json.loads(self.cors_origins)
        if self.app_env in ("production", "staging"):
            # In production/staging, reject wildcard and require explicit origins
            if "*" in origins:
                raise ValueError("Wildcard CORS origin (*) not allowed in production with credentials")
            if not origins:
                raise ValueError("cors_origins must be explicitly configured for production")
        return origins

    @computed_field
    @property
    def effective_cookie_secure(self) -> bool:
        if self.app_env in ("production", "staging"):
            return True
        return self.auth_cookie_secure

    @computed_field
    @property
    def effective_cookie_samesite(self) -> str:
        if self.app_env in ("production", "staging"):
            return "strict"
        return self.auth_cookie_samesite

    @computed_field
    @property
    def effective_cors_allow_credentials(self) -> bool:
        # Only allow credentials with explicit origins (never with wildcard)
        if self.app_env in ("production", "staging"):
            origins = json.loads(self.cors_origins)
            if "*" in origins:
                raise ValueError("Wildcard CORS origin (*) not allowed with credentials in production")
            return len(origins) > 0
        return True

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()


def _get_vault_client():
    return hvac.Client(url=settings.vault_addr, token=settings.vault_token)


def check_vault_health() -> bool:
    try:
        client = _get_vault_client()
        return client.sys.is_initialized() and not client.sys.is_sealed()
    except Exception:
        return False


def configure_secrets(target=None) -> None:
    s = target if target is not None else settings
    if s.app_env == "testing":
        s.jwt_access_secret = "test-access-secret-for-unit-tests"
        s.jwt_refresh_secret = "test-refresh-secret-for-unit-tests"
        return

    client = hvac.Client(url=s.vault_addr, token=s.vault_token)
    try:
        initialized = client.sys.is_initialized()
        sealed = client.sys.is_sealed()
    except Exception as e:
        raise RuntimeError(f"Vault is unreachable at {s.vault_addr}: {e}") from e

    if not initialized:
        raise RuntimeError("Vault is not initialized — cannot load secrets")
    if sealed:
        raise RuntimeError("Vault is sealed — cannot load secrets")

    try:
        secret = client.secrets.kv.v2.read_secret_version(
            path="jwt", mount_point="akarai"
        )
        data = secret["data"]["data"]
        s.jwt_access_secret = data["access_secret"]
        s.jwt_refresh_secret = data["refresh_secret"]
    except hvac.exceptions.InvalidPath:
        raise RuntimeError("Vault secret akarai/jwt not found — has vault-init run?") from None
    except Exception as e:
        raise RuntimeError(f"Failed to read secret akarai/jwt from Vault: {e}") from e
