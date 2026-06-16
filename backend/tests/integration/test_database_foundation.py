import pytest
from sqlalchemy import text

from app.common.database import (
    async_session_factory,
    check_database_connectivity,
    check_pgvector_enabled,
)


@pytest.mark.anyio
class TestDatabaseFoundation:
    @pytest.mark.integration
    async def test_database_connectivity(self):
        result = await check_database_connectivity()
        assert result is True

    @pytest.mark.integration
    async def test_pgvector_extension(self):
        result = await check_pgvector_enabled()
        assert result is True

    @pytest.mark.integration
    async def test_session_execute(self):
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1
