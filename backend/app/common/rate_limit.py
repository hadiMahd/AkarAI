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

    await redis_set(key, str(count + 1), ttl=window)
    return True


AUTH_RATE_LIMITS = {
    "login": {"max_requests": 10, "window_seconds": 300},
    "refresh": {"max_requests": 30, "window_seconds": 300},
    "logout": {"max_requests": 30, "window_seconds": 300},
    "password_reset": {"max_requests": 5, "window_seconds": 600},
    "session_revoke": {"max_requests": 20, "window_seconds": 300},
    "employee_deactivate": {"max_requests": 10, "window_seconds": 300},
}


async def check_auth_rate_limit(
    action: str,
    identifier: str,
) -> bool:
    limits = AUTH_RATE_LIMITS.get(action, {"max_requests": 30, "window_seconds": 300})
    return await check_rate_limit(
        key_type=f"auth:{action}",
        identifier=identifier,
        max_requests=limits["max_requests"],
        window_seconds=limits["window_seconds"],
    )


SEARCH_RATE_LIMITS = {
    "manual": {
        "max_requests": settings.search_manual_rate_limit_max_requests,
        "window_seconds": settings.search_manual_rate_limit_window_seconds,
    },
    "ai_text": {
        "max_requests": settings.search_ai_text_rate_limit_max_requests,
        "window_seconds": settings.search_ai_text_rate_limit_window_seconds,
    },
    "voice": {
        "max_requests": settings.search_voice_rate_limit_max_requests,
        "window_seconds": settings.search_voice_rate_limit_window_seconds,
    },
}


async def check_search_rate_limit(search_mode: str, identifier: str) -> bool:
    limits = SEARCH_RATE_LIMITS.get(search_mode, {"max_requests": 30, "window_seconds": 60})
    return await check_rate_limit(
        key_type=f"search:{search_mode}",
        identifier=identifier,
        max_requests=limits["max_requests"],
        window_seconds=limits["window_seconds"],
    )


PHASE4_RATE_LIMITS = {
    "search": {"max_requests": 30, "window_seconds": 60},
    "inquiry": {"max_requests": 5, "window_seconds": 600},
    "viewing_booking": {"max_requests": 10, "window_seconds": 300},
}


async def check_phase4_rate_limit(
    action: str,
    identifier: str,
) -> bool:
    limits = PHASE4_RATE_LIMITS.get(action, {"max_requests": 30, "window_seconds": 60})
    return await check_rate_limit(
        key_type=f"phase4:{action}",
        identifier=identifier,
        max_requests=limits["max_requests"],
        window_seconds=limits["window_seconds"],
    )
