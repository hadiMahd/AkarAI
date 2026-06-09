from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = True
    project_name: str = "AkarAI"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    database_url: str = "postgresql+asyncpg://akarai:akarai@pgbouncer:6432/akarai"
    database_sync_url: str = "postgresql+psycopg2://akarai:akarai@pgbouncer:6432/akarai"

    redis_url: str = "redis://redis:6379/0"

    minio_endpoint: str = "minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_rag: str = "rag-vault"
    minio_bucket_media: str = "property-media"

    cors_origins: str = '["http://localhost:3000","http://localhost:3001","http://localhost:8501"]'

    vault_addr: str = "http://vault:8200"
    vault_token: str = "root"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
