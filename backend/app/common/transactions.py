from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import async_session_factory


@asynccontextmanager
async def transaction(session: AsyncSession | None = None) -> AsyncGenerator[AsyncSession, None]:
    """Unit-of-work transaction helper.

    Commits on successful block exit, rolls back on exception.
    Accepts an existing session or creates a new one.
    """
    own_session = session is None
    if own_session:
        session = async_session_factory()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        if own_session:
            await session.close()
