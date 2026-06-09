"""AkarAI Worker — DB outbox polling, job registry, event dispatch.

Phase 2: Replaces Redis polling with database outbox_events polling.
No business handlers — foundation.test is the only registered handler.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from typing import Callable

import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://akarai:akarai@pgbouncer:6432/akarai")
PG_URL = DATABASE_URL.replace("+asyncpg", "")

shutdown_flag = False


def _handle_signal() -> None:
    global shutdown_flag
    logger.info("Received shutdown signal — draining...")
    shutdown_flag = True


for _sig in (signal.SIGTERM, signal.SIGINT):
    try:
        signal.signal(_sig, lambda s, f: _handle_signal())
    except Exception:
        pass

JOBS: dict[str, Callable] = {}


def register_job(name: str):
    def decorator(fn):
        JOBS[name] = fn
        return fn
    return decorator


@register_job("ping")
def ping_job():
    return "pong"


@register_job("health")
def health_job() -> dict:
    return {"status": "ok", "worker": "akarai-worker", "jobs": list(JOBS.keys())}


EVENT_HANDLERS: dict[str, Callable] = {}


def register_event_handler(event_name: str):
    def decorator(fn):
        EVENT_HANDLERS[event_name] = fn
        return fn
    return decorator


@register_event_handler("foundation.test")
def _foundation_test_handler(payload: dict) -> None:
    logger.info("foundation.test handler invoked with payload: %s", payload)


async def _poll_loop() -> None:
    from outbox import claim_and_dispatch

    conn = await asyncpg.connect(PG_URL, statement_cache_size=0)
    logger.info("Connected to database for outbox polling")

    try:
        while not shutdown_flag:
            try:
                processed = await claim_and_dispatch(conn, EVENT_HANDLERS)
                if not processed:
                    await asyncio.sleep(1)
            except Exception:
                logger.exception("Unexpected polling error — retrying in 5s")
                await asyncio.sleep(5)
    finally:
        await conn.close()
        logger.info("Database connection closed")


def main() -> None:
    logger.info("AkarAI Worker starting (DB outbox mode)")
    logger.info("Database URL: %s", DATABASE_URL)
    logger.info("Registered jobs: %s", list(JOBS.keys()))
    logger.info("Registered handlers: %s", list(EVENT_HANDLERS.keys()))

    try:
        asyncio.run(_poll_loop())
    except KeyboardInterrupt:
        pass

    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
