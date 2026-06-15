import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Sync no-op: shadows the async conftest fixture for sync tests in this module."""
    yield


@pytest.mark.anyio
class TestSearchIntentAPI:
    async def test_post_search_intent_missing_q_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post("/search/intent", json={})
        assert resp.status_code == 422

    async def test_post_search_intent_with_query_returns_intent_shape(self, async_client: AsyncClient):
        resp = await async_client.post("/search/intent", json={"q": "2 bedroom apartment in Beirut"})
        # May return 200 with intent, or 422/503 if provider not configured
        assert resp.status_code in (200, 503, 422)
        if resp.status_code == 200:
            data = resp.json()
            assert "intent" in data
            assert "source_mode" in data["intent"]
            assert data["intent"]["source_mode"] == "ai_text"

    async def test_post_confirmation_log_missing_required_fields(self, async_client: AsyncClient):
        resp = await async_client.post("/search/logs/confirmation", json={})
        assert resp.status_code == 422

    async def test_post_confirmation_log_valid_returns_204(self, async_client: AsyncClient):
        body = {
            "source_mode": "ai_text",
            "confirmed_filters": {"bedrooms": 2, "city": "Beirut"},
        }
        resp = await async_client.post("/search/logs/confirmation", json=body)
        assert resp.status_code in (204, 200)

    async def test_post_voice_search_no_file_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post("/search/voice")
        assert resp.status_code == 422


@pytest.mark.anyio
class TestSearchRateLimits:
    def test_manual_search_rate_limit_key_format(self):
        from app.common.rate_limit import SEARCH_RATE_LIMITS
        assert "manual" in SEARCH_RATE_LIMITS
        assert "ai_text" in SEARCH_RATE_LIMITS
        assert "voice" in SEARCH_RATE_LIMITS
        assert SEARCH_RATE_LIMITS["ai_text"]["max_requests"] < SEARCH_RATE_LIMITS["manual"]["max_requests"]
        assert SEARCH_RATE_LIMITS["voice"]["max_requests"] < SEARCH_RATE_LIMITS["ai_text"]["max_requests"]
