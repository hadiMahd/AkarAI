"""Seed Vault with secrets from .env file. No env-var leakage in docker logs."""

import os
import secrets
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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[seed] FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
