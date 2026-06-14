import os
import sys

import pytest

_worker_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _worker_root not in sys.path:
    sys.path.insert(0, _worker_root)

_backend_root = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if os.path.isdir(_backend_root):
    sys.path.insert(0, os.path.abspath(_backend_root))

import app.agencies.models  # noqa: F401 - load agency_tenants metadata for RAG FK resolution
