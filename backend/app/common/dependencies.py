from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


def pagination_params(page: int = 1, page_size: int = 20) -> dict:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    return {"page": page, "page_size": page_size, "offset": (page - 1) * page_size, "limit": page_size}
