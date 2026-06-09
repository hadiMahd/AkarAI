def test_worker_job_registry():
    import main as wm

    assert "ping" in wm.JOBS
    assert "health" in wm.JOBS
    assert wm.JOBS["ping"]() == "pong"

    health = wm.JOBS["health"]()
    assert health["status"] == "ok"
    assert "akarai-worker" == health["worker"]


def test_worker_known_events():
    import main as wm

    assert "lead.created" in wm.KNOWN_EVENT_NAMES
    assert "email.notification_requested" in wm.KNOWN_EVENT_NAMES
    assert len(wm.KNOWN_EVENT_NAMES) == 6


def test_worker_handler_registry():
    import main as wm

    # No business handlers registered in Phase 2
    assert len(wm.EVENT_HANDLERS) == 0
