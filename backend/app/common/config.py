import json
from pathlib import Path
from typing import Optional, List

import hvac
from pydantic import AliasChoices, Field, field_validator, computed_field
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
    minio_public_url: str = "localhost:9000"
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

    # Hugging Face (secret loaded from Vault at startup via configure_secrets())
    hf_token: str = ""

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
    ai_guardrails_enabled: bool = True
    ai_pii_redaction_enabled: bool = True
    ai_guardrails_use_nemo_runtime: bool = False
    ai_guardrails_config_path: str = ""
    ai_guardrails_max_history_turns: int = 4
    ai_guardrails_max_message_chars: int = 4000
    azure_openai_endpoint: str = ""
    azure_openai_chat_deployment: str = ""
    azure_openai_embedding_deployment: str = ""
    azure_whisper_deployment: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_embedding_model: str = "text-embedding-3-small"
    azure_openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_rerank_model: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_RERANK_MODEL", "OPENROUTER_RERANKER_MODEL"),
    )
    openrouter_content_safety_model: str = ""
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

    # Media processing settings
    media_max_file_size_mb: int = 10
    media_allowed_content_types: str = "image/jpeg,image/png,image/webp"
    media_internal_prefix: str = "listing-photos/originals"
    media_derivative_prefix: str = "listing-photos/derivatives"
    media_nsfw_threshold: float = 0.75
    media_blur_threshold: float = 208.12155306730278
    media_derivative_max_width: int = 1920
    media_derivative_quality: int = 85
    media_bucket: str = "property-media"

    # Search rate limits
    search_manual_rate_limit_max_requests: int = 30
    search_manual_rate_limit_window_seconds: int = 60
    search_ai_text_rate_limit_max_requests: int = 10
    search_ai_text_rate_limit_window_seconds: int = 60
    search_voice_rate_limit_max_requests: int = 5
    search_voice_rate_limit_window_seconds: int = 60
    # Voice upload
    voice_max_file_size_mb: int = 10
    voice_allowed_content_types: str = "audio/wav,audio/mpeg,audio/mp4,audio/webm,audio/ogg"
    voice_request_timeout_seconds: int = 30

    # RAG ingestion settings
    rag_fastcdc_min_size: int = 256
    rag_fastcdc_avg_size: int = 768
    rag_fastcdc_max_size: int = 1536
    rag_fastcdc_fat: bool = True
    rag_retry_base_seconds: int = 5
    rag_retry_max_seconds: int = 300
    rag_max_file_size_mb: int = 50
    rag_chat_redis_ttl_seconds: int = 86400

    @computed_field
    @property
    def effective_guardrails_config_path(self) -> str:
        if self.ai_guardrails_config_path:
            return self.ai_guardrails_config_path
        default_path = Path(__file__).resolve().parents[1] / "ai" / "guardrails_configs" / "policy_qa"
        return str(default_path)

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
        # In testing, HF token is optional — tests can inject if needed
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

    # Load JWT secrets
    try:
        secret = client.secrets.kv.v2.read_secret_version(
            path="jwt", mount_point="akarai", raise_on_deleted_version=True
        )
        data = secret["data"]["data"]
        s.jwt_access_secret = data["access_secret"]
        s.jwt_refresh_secret = data["refresh_secret"]
    except hvac.exceptions.InvalidPath:
        raise RuntimeError("Vault secret akarai/jwt not found — has vault-init run?") from None
    except Exception as e:
        raise RuntimeError(f"Failed to read secret akarai/jwt from Vault: {e}") from e

    # Load Hugging Face token (optional — moderation will fail-closed if missing)
    try:
        secret = client.secrets.kv.v2.read_secret_version(
            path="ai", mount_point="akarai", raise_on_deleted_version=True
        )
        data = secret["data"]["data"]
        s.hf_token = data.get("hf_token", "")
    except hvac.exceptions.InvalidPath:
        # akarai/ai is optional — moderation will fail-closed if token not configured
        s.hf_token = ""
    except Exception as e:
        raise RuntimeError(f"Failed to read secret akarai/ai from Vault: {e}") from e

    # Load Azure OpenAI config (optional — provider will fail-closed if required fields are missing)
    try:
        secret = client.secrets.kv.v2.read_secret_version(
            path="azure", mount_point="akarai", raise_on_deleted_version=True
        )
        data = secret["data"]["data"]
        s.azure_openai_endpoint = data.get("endpoint", s.azure_openai_endpoint)
        s.azure_openai_chat_deployment = data.get(
            "chat_deployment", s.azure_openai_chat_deployment
        )
        s.azure_openai_embedding_deployment = data.get(
            "embedding_deployment", s.azure_openai_embedding_deployment
        )
        s.azure_whisper_deployment = data.get(
            "whisper_deployment", s.azure_whisper_deployment
        )
        s.azure_openai_embedding_model = data.get(
            "embedding_model", s.azure_openai_embedding_model
        )
        s.azure_openai_api_key = data.get("api_key", "")
    except hvac.exceptions.InvalidPath:
        s.azure_openai_endpoint = s.azure_openai_endpoint
        s.azure_openai_chat_deployment = s.azure_openai_chat_deployment
        s.azure_openai_embedding_deployment = s.azure_openai_embedding_deployment
        s.azure_whisper_deployment = s.azure_whisper_deployment
        s.azure_openai_embedding_model = s.azure_openai_embedding_model
        s.azure_openai_api_key = ""
    except Exception as e:
        raise RuntimeError(f"Failed to read secret akarai/azure from Vault: {e}") from e

    # Load OpenRouter config (optional — reranker will fail-closed if not configured)
    try:
        secret = client.secrets.kv.v2.read_secret_version(
            path="openrouter", mount_point="akarai", raise_on_deleted_version=True
        )
        data = secret["data"]["data"]
        api_key = data.get("api_key", "").strip()
        base_url = data.get("base_url", "").strip()
        rerank_model = data.get("rerank_model", "").strip()
        content_safety_model = data.get("content_safety_model", "").strip()
        if api_key:
            s.openrouter_api_key = api_key
        if base_url:
            s.openrouter_base_url = base_url
        if rerank_model:
            s.openrouter_rerank_model = rerank_model
        if content_safety_model:
            s.openrouter_content_safety_model = content_safety_model
    except hvac.exceptions.InvalidPath:
        s.openrouter_api_key = s.openrouter_api_key
        s.openrouter_base_url = s.openrouter_base_url
        s.openrouter_rerank_model = s.openrouter_rerank_model
        s.openrouter_content_safety_model = s.openrouter_content_safety_model
    except Exception as e:
        raise RuntimeError(f"Failed to read secret akarai/openrouter from Vault: {e}") from e
