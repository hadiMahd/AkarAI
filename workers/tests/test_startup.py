import subprocess
import sys


def test_worker_main_imports():
    import main

    assert hasattr(main, "JOBS")
    assert "ping" in main.JOBS
    assert "health" in main.JOBS


def test_ping_job():
    from main import JOBS

    assert JOBS["ping"]() == "pong"


def test_health_job():
    from main import JOBS

    result = JOBS["health"]()
    assert result["status"] == "ok"
    assert result["worker"] == "akarai-worker"
    assert "jobs" in result
