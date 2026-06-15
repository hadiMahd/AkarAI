import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository


pytestmark = pytest.mark.anyio


class DummyRepository(BaseRepository):
    pass


class TestBaseRepository:
    async def test_repository_stores_session(self):
        session = object()
        repo = DummyRepository(session)
        assert repo.session is session

    async def test_subclass_inherits_session(self):
        session = object()

        class CustomRepo(BaseRepository):
            pass

        repo = CustomRepo(session)
        assert repo.session is session
