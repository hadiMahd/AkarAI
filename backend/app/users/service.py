from datetime import datetime, timezone

from app.users.repository import UsersRepository, User


class UsersService:
    def __init__(self, repository: UsersRepository):
        self._repo = repository

    async def get_user(self, user_id: str) -> User | None:
        return await self._repo.get_user_by_id(user_id)

    async def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        await self._repo.update_user(user)

    async def update_password(self, user: User, new_password_hash: str) -> None:
        user.password_hash = new_password_hash
        user.password_changed_at = datetime.now(timezone.utc)
        await self._repo.update_user(user)
