from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.common.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.pgbouncer_database_url,
    echo=settings.app_debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connectivity() -> bool:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def check_pgvector_enabled() -> bool:
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            row = result.fetchone()
            return row is not None
    except Exception:
        return False
