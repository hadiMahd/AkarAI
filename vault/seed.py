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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[seed] FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
