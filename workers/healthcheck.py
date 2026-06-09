"""Healthcheck script for the worker container. Exits 0 if DB reachable."""

import asyncio
import asyncpg

DB_URL = "postgresql://akarai:akarai@pgbouncer:6432/akarai"


async def _check() -> None:
    conn = await asyncpg.connect(DB_URL, statement_cache_size=0)
    await conn.close()


def main() -> None:
    asyncio.run(_check())


if __name__ == "__main__":
    main()
