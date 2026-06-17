from datetime import datetime, timezone

from app.users.repository import UsersRepository, User
from app.common.exceptions import NotFoundError
from app.users.schemas import UserProfileResponse


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

    @staticmethod
    def get_lead_profile_missing_fields(user: User) -> list[str]:
        missing_fields: list[str] = []
        if not user.name or not user.name.strip():
            missing_fields.append("name")
        has_email = bool(user.email and user.email.strip())
        has_phone = bool(user.phone and user.phone.strip())
        if not has_email and not has_phone:
            missing_fields.append("contact")
        return missing_fields

    def build_profile_response(self, user: User) -> UserProfileResponse:
        missing_fields = self.get_lead_profile_missing_fields(user)
        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            phone=user.phone,
            is_complete_for_leads=not missing_fields,
            missing_fields=missing_fields,
        )

    async def get_profile(self, user_id: str) -> UserProfileResponse:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError(detail="User not found")
        return self.build_profile_response(user)

    async def update_profile(self, user_id: str, data: dict) -> UserProfileResponse:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError(detail="User not found")

        if "name" in data:
            user.name = data["name"]
        if "phone" in data:
            user.phone = data["phone"]

        await self._repo.update_user(user)
        return self.build_profile_response(user)
