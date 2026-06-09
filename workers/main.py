import logging
import os
import signal
import sys
import time
from typing import Callable

import redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
shutdown_flag = False


def handle_signal(signum: int, _frame) -> None:
    global shutdown_flag
    logger.info("Received signal %d, shutting down gracefully...", signum)
    shutdown_flag = True


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

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


# ---------------------------------------------------------------------------
# Phase 2: Outbox event polling foundation (no business event handlers)
# ---------------------------------------------------------------------------

KNOWN_EVENT_NAMES = [
    "lead.created",
    "viewing.scheduled",
    "viewing.cancelled",
    "rag.document_uploaded",
    "listing.image_uploaded",
    "email.notification_requested",
]

EVENT_HANDLERS: dict[str, Callable] = {}


def register_event_handler(event_name: str):
    def decorator(fn):
        EVENT_HANDLERS[event_name] = fn
        return fn
    return decorator


async def poll_outbox(client: redis.Redis):
    """Poll outbox events from Redis list and dispatch to registered handlers.

    In production this polls the database outbox_events table. Phase 2 uses
    Redis as a lightweight polling transport until a proper queue is selected.
    """
    while not shutdown_flag:
        try:
            event_data = client.lpop("akarai:outbox:queue")
            if event_data:
                import json
                event = json.loads(event_data)
                event_name = event.get("event_name", "unknown")
                handler = EVENT_HANDLERS.get(event_name)
                if handler:
                    logger.info("Dispatching event %s", event_name)
                    handler(event)
                else:
                    logger.debug("No handler for event %s (expected in Phase 2)", event_name)
        except Exception as e:
            logger.error("Outbox poll error: %s", e)
        time.sleep(1)


def main():
    logger.info("AkarAI Worker starting...")

    try:
        r = redis.from_url(redis_url, socket_connect_timeout=5)
        r.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error("Failed to connect to Redis: %s", e)
        sys.exit(1)

    logger.info("Registered jobs: %s", list(JOBS.keys()))
    logger.info("Registered event handlers: %s", list(EVENT_HANDLERS.keys()))
    logger.info("Known event names (Phase 2 foundation): %s", KNOWN_EVENT_NAMES)

    while not shutdown_flag:
        time.sleep(1)

    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
