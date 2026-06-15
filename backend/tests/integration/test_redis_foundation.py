import pytest

from app.common.redis import (
    check_redis_connectivity,
    redis_delete,
    redis_exists,
    redis_get,
    redis_set,
)


@pytest.mark.anyio
class TestRedisFoundation:
    @pytest.mark.integration
    async def test_redis_connectivity(self):
        result = await check_redis_connectivity()
        assert result is True

    @pytest.mark.integration
    async def test_redis_set_and_get(self):
        await redis_set("__test_key__", "hello", ttl=10)
        value = await redis_get("__test_key__")
        assert value == "hello"
        await redis_delete("__test_key__")

    @pytest.mark.integration
    async def test_redis_exists(self):
        await redis_set("__test_exists__", "1", ttl=10)
        assert await redis_exists("__test_exists__") is True
        assert await redis_exists("__nonexistent__") is False
        await redis_delete("__test_exists__")

    @pytest.mark.integration
    async def test_redis_delete(self):
        await redis_set("__test_del__", "x", ttl=10)
        await redis_delete("__test_del__")
        assert await redis_exists("__test_del__") is False
