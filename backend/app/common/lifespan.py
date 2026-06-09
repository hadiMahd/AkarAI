import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.common.config import settings
from app.common.database import engine
from app.common.logging import setup_logging
from app.common.redis import close_redis, get_redis

_initialised = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _initialised

    setup_logging()
    logger = logging.getLogger(__name__)

    if not _initialised:
        logger.info(
            "Starting %s (env=%s, debug=%s)",
            settings.project_name,
            settings.app_env,
            settings.app_debug,
        )
        _initialised = True

    try:
        await get_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning("Redis not available at startup: %s", e)

    yield

    logger.info("Shutting down...")
    await close_redis()
    await engine.dispose()
    logger.info("Shutdown complete")
