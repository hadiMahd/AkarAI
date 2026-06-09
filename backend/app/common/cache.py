import json
from typing import Optional

from app.common.redis import redis_delete, redis_get, redis_set


def _cache_key(namespace: str, key: str) -> str:
    return f"cache:{namespace}:{key}"


async def cache_get(namespace: str, key: str) -> Optional[dict]:
    raw = await redis_get(_cache_key(namespace, key))
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(namespace: str, key: str, value: dict, ttl: int = 300) -> None:
    await redis_set(_cache_key(namespace, key), json.dumps(value), ttl=ttl)


async def cache_delete(namespace: str, key: str) -> None:
    await redis_delete(_cache_key(namespace, key))


async def cache_invalidate_namespace(namespace: str) -> None:
    # Pattern-based invalidation requires SCAN; stub for Phase 2.
    pass
