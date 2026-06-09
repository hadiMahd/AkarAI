from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repository import BaseRepository
from app.users.models import User
from app.auth.models import RefreshSession


class AuthRepository(BaseRepository):
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_refresh_session(self, session: RefreshSession) -> RefreshSession:
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_refresh_session_by_token_hash(self, token_hash: str) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_refresh_session_by_id(self, session_id: str) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(RefreshSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_sessions_for_user(self, user_id: str) -> list[RefreshSession]:
        result = await self.session.execute(
            select(RefreshSession).where(
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > RefreshSession.issued_at,
            )
        )
        return list(result.scalars().all())

    async def update_refresh_session(self, session: RefreshSession) -> RefreshSession:
        self.session.add(session)
        await self.session.flush()
        return session
