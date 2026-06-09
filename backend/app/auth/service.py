import uuid
from datetime import datetime, timezone

from app.common.redis import redis_delete, redis_get, redis_set


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    key = f"blacklist:jti:{jti}"
    await redis_set(key, "1", ttl=ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    key = f"blacklist:jti:{jti}"
    return await redis_get(key) is not None


async def invalidate_user_sessions(user_id: str) -> None:
    marker = f"session_invalidated:{user_id}:{uuid.uuid4().hex[:12]}"
    await redis_set(marker, str(datetime.now(timezone.utc)), ttl=86400 * 7)
