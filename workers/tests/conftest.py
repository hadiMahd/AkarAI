import os
import sys

import pytest

_backend_root = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if os.path.isdir(_backend_root):
    sys.path.insert(0, os.path.abspath(_backend_root))

import app.agencies.models  # noqa: F401 - load agency_tenants metadata for RAG FK resolution


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
