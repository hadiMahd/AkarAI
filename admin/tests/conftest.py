"""Shared fixtures for the admin/ Streamlit test suite.

These tests intentionally do not require Docker or the backend database.
They mock the ``requests`` calls made through ``admin.api_client`` and
patch the Streamlit ``st`` module where needed.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import types

import pytest


HERE = os.path.dirname(os.path.abspath(__file__))
ADMIN_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(ADMIN_DIR, ".."))

# Support both nested (host) and flat (container) layouts.
# Test imports use ``from admin.xxx import ...`` which works when
# repo root contains an ``admin/`` package. In a Docker container
# the admin/ modules are copied flat into the workdir, so we alias
# ``admin.<module>`` to the corresponding top-level module.
if not os.path.isdir(os.path.join(ADMIN_DIR, "api_client")) and os.path.isfile(
    os.path.join(ADMIN_DIR, "api_client.py")
):
    # Container layout: files are flat in ADMIN_DIR (/app).
    # Expose the top-level modules as "admin.api_client", "admin.auth", etc.
    _ADMIN_MODULES = (
        "api_client",
        "auth",
        "components",
        "insights_view",
        "audit_logs_view",
        "rag_evals_view",
        "role_access_view",
    )
    _admin_pkg = types.ModuleType("admin")
    _admin_pkg.__path__ = [ADMIN_DIR]  # type: ignore[attr-defined]
    sys.modules["admin"] = _admin_pkg
    for _name in _ADMIN_MODULES:
        _mod = importlib.import_module(_name)
        setattr(_admin_pkg, _name, _mod)
        sys.modules[f"admin.{_name}"] = _mod
    _app_mod = importlib.import_module("app")
    setattr(_admin_pkg, "app", _app_mod)
    sys.modules["admin.app"] = _app_mod

sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, ADMIN_DIR)


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch):
    """Pin a stable backend URL for every test and ensure clean env."""
    monkeypatch.setenv("BACKEND_URL", "http://backend.test:8000")
    monkeypatch.setenv("APP_ENV", "testing")
    yield


class FakeResponse:
    """Minimal ``requests.Response``-like object for unit tests."""

    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text or ""
        self.content = b"" if not payload else json.dumps(payload).encode()

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")
