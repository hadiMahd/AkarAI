"""Healthcheck script for the worker container. Exits 0 if DB reachable."""

import asyncio
import os

import asyncpg

DB_URL = os.getenv("DATABASE_URL").replace("+asyncpg", "")


async def _check() -> None:
    conn = await asyncpg.connect(DB_URL, statement_cache_size=0)
    await conn.close()


def main() -> None:
    asyncio.run(_check())


if __name__ == "__main__":
    main()
