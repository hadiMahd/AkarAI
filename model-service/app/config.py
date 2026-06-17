import os
from pydantic_settings import BaseSettings


class ModelServiceSettings(BaseSettings):
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8100
    backend_url: str = "http://backend:8000"
    callback_token: str = ""
    redis_url: str = "redis://redis:6379/0"
    request_timeout_seconds: int = 120
    retry_max_attempts: int = 3
    retry_base_delay_seconds: int = 5
    retry_max_delay_seconds: int = 120

    # Spam classifier stage (sklearn Pipeline including TfidfVectorizer)
    spam_pipeline_path: str = "artifacts/spam_pipeline.joblib"
    spam_threshold: float = 0.5
    empty_message_is_spam: bool = True

    # Hot/Normal ranker stage (HuggingFace ModernBERT transformer)
    level_transformer_path: str = "artifacts/level_transformer"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = ModelServiceSettings()
