import logging
import os
import signal
import sys
import time

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
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_flag = True


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

JOBS = {}


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


def main():
    logger.info("AkarAI Worker starting...")

    try:
        r = redis.from_url(redis_url, socket_connect_timeout=5)
        r.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)

    logger.info(f"Registered jobs: {list(JOBS.keys())}")

    while not shutdown_flag:
        time.sleep(1)

    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
