from typing import Optional

from redis.asyncio import Redis

from app.common.config import settings

_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def check_redis_connectivity() -> bool:
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False


async def redis_set(key: str, value: str, ttl: Optional[int] = None) -> None:
    client = await get_redis()
    await client.set(key, value, ex=ttl)


async def redis_get(key: str) -> Optional[str]:
    client = await get_redis()
    return await client.get(key)


async def redis_delete(key: str) -> None:
    client = await get_redis()
    await client.delete(key)


async def redis_exists(key: str) -> bool:
    client = await get_redis()
    return await client.exists(key) > 0


async def redis_scan_delete(pattern: str) -> int:
    client = await get_redis()
    deleted = 0
    cursor = 0
    while True:
        cursor, keys = await client.scan(cursor, match=pattern, count=100)
        if keys:
            deleted += await client.delete(*keys)
        if cursor == 0:
            break
    return deleted
