"""Seed Vault with secrets from .env file. No env-var leakage in docker logs."""

import os
import sys
import time

import hvac
from dotenv import dotenv_values

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
DOTENV_PATH = os.getenv("DOTENV_PATH", "/.env")


def wait_for_vault(client: hvac.Client, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if client.sys.is_initialized() and not client.sys.is_sealed():
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"Vault at {VAULT_ADDR} not healthy after {timeout}s")


def main() -> None:
    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
    print(f"[seed] Waiting for Vault at {VAULT_ADDR}...")
    wait_for_vault(client)
    print("[seed] Vault healthy")

    print("[seed] Enabling akarai kv-v2...")
    try:
        client.sys.enable_secrets_engine(
            backend_type="kv-v2",
            path="akarai",
        )
    except hvac.exceptions.InvalidRequest:
        pass

    dotenv = dotenv_values(DOTENV_PATH)

    # Seed JWT secrets
    access_secret = dotenv.get("JWT_ACCESS_SECRET") or secrets.token_hex(32)
    refresh_secret = dotenv.get("JWT_REFRESH_SECRET") or secrets.token_hex(32)

    jwt_source = []
    if dotenv.get("JWT_ACCESS_SECRET"):
        jwt_source.append("access_secret: .env")
    else:
        jwt_source.append("access_secret: generated")
    if dotenv.get("JWT_REFRESH_SECRET"):
        jwt_source.append("refresh_secret: .env")
    else:
        jwt_source.append("refresh_secret: generated")

    client.secrets.kv.v2.create_or_update_secret(
        path="jwt",
        secret={
            "access_secret": access_secret,
            "refresh_secret": refresh_secret,
        },
        mount_point="akarai",
    )

    print(f"[seed] akarai/jwt seeded ({', '.join(jwt_source)})")

    # Seed AI secrets (Hugging Face token)
    hf_token = dotenv.get("HF_TOKEN", "").strip()
    ai_source = []
    if hf_token:
        ai_source.append("hf_token: .env")
    else:
        ai_source.append("hf_token: not set")

    client.secrets.kv.v2.create_or_update_secret(
        path="ai",
        secret={
            "hf_token": hf_token,
        },
        mount_point="akarai",
    )

    print(f"[seed] akarai/ai seeded ({', '.join(ai_source)})")

    # Seed Azure OpenAI config (optional)
    azure_openai_endpoint = dotenv.get("AZURE_OPENAI_ENDPOINT", "").strip()
    azure_openai_api_key = dotenv.get("AZURE_OPENAI_API_KEY", "").strip()
    azure_openai_chat_deployment = dotenv.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "").strip()
    azure_openai_embedding_deployment = dotenv.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "").strip()
    azure_whisper_deployment = dotenv.get("AZURE_WHISPER_DEPLOYMENT", "").strip()
    azure_openai_embedding_model = dotenv.get("AZURE_OPENAI_EMBEDDING_MODEL", "").strip()
    azure_source = []
    if azure_openai_endpoint:
        azure_source.append("endpoint: .env")
    else:
        azure_source.append("endpoint: not set")
    if azure_openai_api_key:
        azure_source.append("api_key: .env")
    else:
        azure_source.append("api_key: not set")
    if azure_openai_chat_deployment:
        azure_source.append("chat_deployment: .env")
    else:
        azure_source.append("chat_deployment: not set")
    if azure_openai_embedding_deployment:
        azure_source.append("embedding_deployment: .env")
    else:
        azure_source.append("embedding_deployment: not set")
    if azure_whisper_deployment:
        azure_source.append("whisper_deployment: .env")
    else:
        azure_source.append("whisper_deployment: not set")
    if azure_openai_embedding_model:
        azure_source.append("embedding_model: .env")
    else:
        azure_source.append("embedding_model: default/empty")

    client.secrets.kv.v2.create_or_update_secret(
        path="azure",
        secret={
            "endpoint": azure_openai_endpoint,
            "api_key": azure_openai_api_key,
            "chat_deployment": azure_openai_chat_deployment,
            "embedding_deployment": azure_openai_embedding_deployment,
            "whisper_deployment": azure_whisper_deployment,
            "embedding_model": azure_openai_embedding_model,
        },
        mount_point="akarai",
    )

    print(f"[seed] akarai/azure seeded ({', '.join(azure_source)})")

    # Seed OpenRouter reranking config (optional)
    openrouter_api_key = dotenv.get("OPENROUTER_API_KEY", "").strip()
    openrouter_base_url = dotenv.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    openrouter_rerank_model = (
        dotenv.get("OPENROUTER_RERANK_MODEL", "")
        or dotenv.get("OPENROUTER_RERANKER_MODEL", "")
    ).strip()
    openrouter_content_safety_model = dotenv.get("OPENROUTER_CONTENT_SAFETY_MODEL", "").strip()
    openrouter_source = []
    if openrouter_api_key:
        openrouter_source.append("api_key: .env")
    else:
        openrouter_source.append("api_key: not set")
    if openrouter_rerank_model:
        openrouter_source.append("rerank_model: .env")
    else:
        openrouter_source.append("rerank_model: not set")
    if openrouter_content_safety_model:
        openrouter_source.append("content_safety_model: .env")
    else:
        openrouter_source.append("content_safety_model: not set")

    client.secrets.kv.v2.create_or_update_secret(
        path="openrouter",
        secret={
            "api_key": openrouter_api_key,
            "base_url": openrouter_base_url,
            "rerank_model": openrouter_rerank_model,
            "content_safety_model": openrouter_content_safety_model,
        },
        mount_point="akarai",
    )

    print(f"[seed] akarai/openrouter seeded ({', '.join(openrouter_source)})")

    # Seed Azure OCR / Computer Vision config (optional)
    azure_cv_endpoint = (
        dotenv.get("AZURE_CV_ENDPOINT", "")
        or dotenv.get("AZURE_OCR_ENDPOINT", "")
    ).strip()
    azure_cv_api_key = (
        dotenv.get("AZURE_CV_API_KEY", "")
        or dotenv.get("AZURE_OCR_API_KEY", "")
    ).strip()
    azure_cv_source = []
    if azure_cv_endpoint:
        azure_cv_source.append("endpoint: .env")
    else:
        azure_cv_source.append("endpoint: not set")
    if azure_cv_api_key:
        azure_cv_source.append("api_key: .env")
    else:
        azure_cv_source.append("api_key: not set")

    client.secrets.kv.v2.create_or_update_secret(
        path="azure_cv",
        secret={
            "endpoint": azure_cv_endpoint,
            "api_key": azure_cv_api_key,
        },
        mount_point="akarai",
    )

    print(f"[seed] akarai/azure_cv seeded ({', '.join(azure_cv_source)})")

    # Seed Lead Model Service config (optional)
    lead_model_service_url = dotenv.get("LEAD_MODEL_SERVICE_URL", "http://lead-model-service:8100").strip()
    lead_model_service_callback_token = dotenv.get(
        "LEAD_MODEL_SERVICE_CALLBACK_TOKEN",
        "dev-callback-token-do-not-use-in-production",
    ).strip()
    lead_model_source = []
    if dotenv.get("LEAD_MODEL_SERVICE_URL"):
        lead_model_source.append("service_url: .env")
    else:
        lead_model_source.append("service_url: default")
    if dotenv.get("LEAD_MODEL_SERVICE_CALLBACK_TOKEN"):
        lead_model_source.append("callback_token: .env")
    else:
        lead_model_source.append("callback_token: default")

    client.secrets.kv.v2.create_or_update_secret(
        path="lead_model_service",
        secret={
            "service_url": lead_model_service_url,
            "callback_token": lead_model_service_callback_token,
        },
        mount_point="akarai",
    )

    print(f"[seed] akarai/lead_model_service seeded ({', '.join(lead_model_source)})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[seed] FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
