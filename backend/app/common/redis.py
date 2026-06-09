from redis.asyncio import Redis

from app.common.config import settings

redis_client: Redis | None = None


async def get_redis() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def check_redis_connectivity() -> bool:
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False
