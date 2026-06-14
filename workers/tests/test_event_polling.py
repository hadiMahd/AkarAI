def test_worker_job_registry():
    import main as wm
    assert "ping" in wm.JOBS
    assert "health" in wm.JOBS
    assert wm.JOBS["ping"]() == "pong"
    health = wm.JOBS["health"]()
    assert health["status"] == "ok"
    assert "akarai-worker" == health["worker"]


def test_worker_handler_registry():
    import main as wm
    assert set(wm.EVENT_HANDLERS) == {
        "foundation.test",
        "listing.image_uploaded",
        "rag.document_uploaded",
    }


def test_foundation_test_handler_exists():
    import main as wm
    handler = wm.EVENT_HANDLERS["foundation.test"]
    assert callable(handler)
