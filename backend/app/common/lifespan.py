import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.common.config import settings
from app.common.database import engine
from app.common.logging import setup_logging
from app.common.redis import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.project_name} (env={settings.app_env})")

    try:
        await get_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis not available at startup: {e}")

    yield

    logger.info("Shutting down...")
    await close_redis()
    await engine.dispose()
    logger.info("Shutdown complete")
