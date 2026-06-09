from app.common.config import settings
from app.common.redis import redis_set, redis_get


def _rate_limit_key(key_type: str, identifier: str, window: int) -> str:
    return f"ratelimit:{key_type}:{identifier}:{window}"


async def check_rate_limit(
    key_type: str,
    identifier: str,
    max_requests: int | None = None,
    window_seconds: int | None = None,
) -> bool:
    """Returns True if request is allowed, False if rate limit exceeded."""
    max_req = max_requests or settings.rate_limit_default_max_requests
    window = window_seconds or settings.rate_limit_default_window_seconds

    key = _rate_limit_key(key_type, identifier, window)
    current = await redis_get(key)

    if current is None:
        await redis_set(key, "1", ttl=window)
        return True

    count = int(current)
    if count >= max_req:
        return False

    # Increment without resetting TTL (approximate; production needs Lua)
    await redis_set(key, str(count + 1), ttl=window)
    return True
