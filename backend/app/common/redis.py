import asyncio
from typing import Optional

from redis.asyncio import Redis

from app.common.config import settings

_redis_client: Optional[Redis] = None
_redis_loop_id: Optional[int] = None


async def get_redis() -> Redis:
    """Return the shared Redis client, recreating it when the event loop has changed.

    In production there is a single event loop and the client is created once.
    In tests, different async frameworks (anyio/pytest-asyncio) may use distinct
    loop instances; tracking the loop id lets us reset the singleton safely.
    """
    global _redis_client, _redis_loop_id

    try:
        current_loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        current_loop_id = None

    if _redis_client is not None and _redis_loop_id != current_loop_id:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None

    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        _redis_loop_id = current_loop_id

    return _redis_client


async def close_redis() -> None:
    global _redis_client, _redis_loop_id
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        _redis_loop_id = None


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
