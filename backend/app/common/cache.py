import json
from typing import Optional

from app.common.redis import redis_delete, redis_get, redis_set, redis_scan_delete


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
    pattern = _cache_key(namespace, "*")
    await redis_scan_delete(pattern)


LISTING_SEARCH_NAMESPACE = "listing_search"


async def invalidate_listing_search_cache(listing_id: str | None = None) -> None:
    if listing_id:
        await cache_delete(LISTING_SEARCH_NAMESPACE, f"detail:{listing_id}")
    await redis_scan_delete(_cache_key(LISTING_SEARCH_NAMESPACE, "search:*"))
