import pytest
from sqlalchemy import text

from app.common.database import async_session_factory


class TestPgvectorFoundation:
    @pytest.mark.integration
    async def test_pgvector_extension_installed(self):
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            row = result.fetchone()
            assert row is not None, "pgvector extension must be installed"
