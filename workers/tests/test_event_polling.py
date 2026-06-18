import importlib
import sys


def _load_worker_main(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    sys.modules.pop("main", None)
    return importlib.import_module("main")


def test_worker_job_registry(monkeypatch):
    wm = _load_worker_main(monkeypatch)
    assert "ping" in wm.JOBS
    assert "health" in wm.JOBS
    assert wm.JOBS["ping"]() == "pong"
    health = wm.JOBS["health"]()
    assert health["status"] == "ok"
    assert "akarai-worker" == health["worker"]


def test_worker_handler_registry(monkeypatch):
    wm = _load_worker_main(monkeypatch)
    assert {
        "foundation.test",
        "listing.image_uploaded",
        "rag.document_uploaded",
    }.issubset(set(wm.EVENT_HANDLERS))
    assert "agency_ai.spec_sheet_uploaded" in wm.EVENT_HANDLERS
    assert "lead.created" in wm.EVENT_HANDLERS


def test_foundation_test_handler_exists(monkeypatch):
    wm = _load_worker_main(monkeypatch)
    handler = wm.EVENT_HANDLERS["foundation.test"]
    assert callable(handler)
