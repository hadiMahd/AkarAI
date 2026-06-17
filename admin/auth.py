"""Authentication helpers for the Streamlit platform admin app.

The platform admin app reuses the existing backend bearer-token auth.
This module:
- Persists a session token across Streamlit reruns
- Validates that the bearer is a ``platform_admin`` AND has the
  dedicated ``platform:dashboard_read`` permission
- Surfaces a clear ``AuthState`` to the rest of the UI

Streamlit never sees passwords directly. The login form posts via the
shared ``AdminAPIClient`` and the result is cached in
``st.session_state``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
try:
    from streamlit_cookies_manager import EncryptedCookieManager
except ImportError:  # pragma: no cover - exercised only before dependency install
    EncryptedCookieManager = None

from admin.api_client import AdminAPIError, AdminAPIClient


PLATFORM_DASHBOARD_PERMISSION = "platform:dashboard_read"
COOKIE_PREFIX = "akarai_platform_admin/"
TOKEN_COOKIE_KEY = f"{COOKIE_PREFIX}token"
ACTOR_COOKIE_KEY = f"{COOKIE_PREFIX}actor"
COOKIE_PASSWORD = "akarai-admin-cookie-key"


@dataclass(frozen=True)
class AuthState:
    token: str
    actor: dict[str, Any]

    @property
    def email(self) -> str:
        return self.actor.get("email", "")

    @property
    def name(self) -> str:
        return self.actor.get("name") or self.actor.get("email", "")

    @property
    def role(self) -> str:
        return self.actor.get("role", "")

    @property
    def permissions(self) -> list[str]:
        return list(self.actor.get("permissions", []) or [])

    def has_dashboard_access(self) -> bool:
        if self.role != "platform_admin":
            return False
        return PLATFORM_DASHBOARD_PERMISSION in self.permissions


def _session_state() -> dict[str, Any]:
    return st.session_state


def _cookie_password() -> str:
    env_password = os.getenv("ADMIN_COOKIE_PASSWORD")
    if env_password:
        return env_password
    try:
        secrets = st.secrets
        if "ADMIN_COOKIE_PASSWORD" in secrets:
            return str(secrets["ADMIN_COOKIE_PASSWORD"])
    except StreamlitSecretNotFoundError:
        pass
    return COOKIE_PASSWORD


def _get_cookie_store() -> Any | None:
    if EncryptedCookieManager is None:
        return None
    state = _session_state()
    store = state.get("_platform_admin_cookies")
    if store is None:
        store = EncryptedCookieManager(
            prefix=COOKIE_PREFIX,
            password=_cookie_password(),
        )
        state["_platform_admin_cookies"] = store
    return store


def _load_from_cookies() -> AuthState | None:
    cookies = _get_cookie_store()
    if cookies is None or not cookies.ready():
        return None
    token = cookies.get(TOKEN_COOKIE_KEY)
    actor_raw = cookies.get(ACTOR_COOKIE_KEY)
    if not token or not actor_raw:
        return None
    try:
        actor = json.loads(actor_raw)
    except json.JSONDecodeError:
        _clear_cookie_auth()
        return None
    if not isinstance(actor, dict):
        _clear_cookie_auth()
        return None
    state = _session_state()
    state["platform_admin_token"] = token
    state["platform_admin_actor"] = actor
    return AuthState(token=token, actor=actor)


def _persist_cookie_auth(token: str, actor: dict[str, Any]) -> None:
    cookies = _get_cookie_store()
    if cookies is None or not cookies.ready():
        return
    cookies[TOKEN_COOKIE_KEY] = token
    cookies[ACTOR_COOKIE_KEY] = json.dumps(actor)
    cookies.save()


def _clear_cookie_auth() -> None:
    cookies = _get_cookie_store()
    if cookies is None or not cookies.ready():
        return
    cookies.pop(TOKEN_COOKIE_KEY, None)
    cookies.pop(ACTOR_COOKIE_KEY, None)
    cookies.save()


def get_auth_state() -> AuthState | None:
    state = _session_state()
    token = state.get("platform_admin_token")
    actor = state.get("platform_admin_actor")
    if not token or not actor:
        return _load_from_cookies()
    return AuthState(token=token, actor=actor)


def sign_in(client: AdminAPIClient, email: str, password: str) -> AuthState:
    payload = client.login(email=email, password=password)
    token = payload.get("access_token")
    if not token:
        raise AdminAPIError(401, "Login response missing access token", "INVALID_LOGIN")
    actor = payload.get("actor") or client.get_current_actor(token)
    state = _session_state()
    state["platform_admin_token"] = token
    state["platform_admin_actor"] = actor
    _persist_cookie_auth(token, actor)
    return AuthState(token=token, actor=actor)


def sign_out() -> None:
    state = _session_state()
    state.pop("platform_admin_token", None)
    state.pop("platform_admin_actor", None)
    _clear_cookie_auth()


__all__ = [
    "AuthState",
    "PLATFORM_DASHBOARD_PERMISSION",
    "get_auth_state",
    "sign_in",
    "sign_out",
]
