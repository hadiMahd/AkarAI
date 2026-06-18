import os
import socket
import sys
from urllib.parse import urlparse

import pytest

_worker_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _worker_root not in sys.path:
    sys.path.insert(0, _worker_root)

_backend_root = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if os.path.isdir(_backend_root):
    sys.path.insert(0, os.path.abspath(_backend_root))

import app.agencies.models  # noqa: F401 - load agency_tenants metadata for RAG FK resolution


def require_test_database() -> None:
    database_url = os.getenv("DATABASE_URL", "postgresql://akarai:akarai@postgres:5432/akarai")
    parsed = urlparse(database_url.replace("+asyncpg", ""))
    host = parsed.hostname or "postgres"
    port = parsed.port or 5432
    try:
        socket.getaddrinfo(host, port)
    except OSError:
        pytest.skip(f"Test database host is unreachable from this environment: {host}:{port}")
