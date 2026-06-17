import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_infra():
    """Sync no-op: shadows the async session-scoped conftest fixture.

    Unit tests do not need Redis cleanup or engine disposal at session
    boundaries — they either mock infrastructure entirely or run against
    an in-process DB that the outer conftest already set up.
    """
    yield


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Sync no-op: shadows the async function-scoped conftest fixture.

    Unit tests that check rate-limiting keys assert on the key-building
    logic itself, not on live Redis state.
    """
    yield
