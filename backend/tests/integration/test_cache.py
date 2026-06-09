import pytest

from app.common.cache import cache_delete, cache_get, cache_set


class TestCache:
    @pytest.mark.integration
    async def test_cache_set_and_get(self):
        await cache_set("test", "key1", {"hello": "world"}, ttl=10)
        result = await cache_get("test", "key1")
        assert result == {"hello": "world"}
        await cache_delete("test", "key1")

    @pytest.mark.integration
    async def test_cache_miss(self):
        result = await cache_get("test", "nonexistent-key")
        assert result is None

    @pytest.mark.integration
    async def test_cache_delete(self):
        await cache_set("test", "del-key", {"x": 1}, ttl=10)
        await cache_delete("test", "del-key")
        assert await cache_get("test", "del-key") is None
