import pytest
from sqlalchemy import text

from app.common.database import async_session_factory
from app.common.transactions import transaction


@pytest.mark.anyio
class TestTransactions:
    @pytest.mark.integration
    async def test_transaction_commit(self):
        async with transaction() as session:
            await session.execute(text("SELECT 1"))
        # Session closed after commit — no exception means success

    @pytest.mark.integration
    async def test_transaction_rollback_on_error(self):
        class TestError(Exception):
            pass

        async with async_session_factory() as session:
            await session.execute(text("CREATE TABLE IF NOT EXISTS _tx_test (id SERIAL PRIMARY KEY, val TEXT)"))
            await session.commit()

        try:
            async with transaction() as session:
                await session.execute(text("INSERT INTO _tx_test (val) VALUES ('should_rollback')"))
                raise TestError("deliberate failure")
        except TestError:
            pass

        async with async_session_factory() as session:
            result = await session.execute(text("SELECT count(*) FROM _tx_test"))
            count = result.fetchone()[0]
            assert count == 0

        async with async_session_factory() as session:
            await session.execute(text("DROP TABLE IF EXISTS _tx_test"))
            await session.commit()

    @pytest.mark.integration
    async def test_transaction_with_existing_session(self):
        async with async_session_factory() as session:
            async with transaction(session) as tx_session:
                assert tx_session is session
