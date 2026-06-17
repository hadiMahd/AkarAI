from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_actor
from app.common.dependencies import get_db_session
from app.users.repository import UsersRepository
from app.users.schemas import UserProfileResponse, UserProfileUpdateRequest
from app.users.service import UsersService

router = APIRouter(tags=["Users"])


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    service = UsersService(UsersRepository(db))
    return await service.get_profile(actor["user_id"])


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    body: UserProfileUpdateRequest,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db_session),
):
    service = UsersService(UsersRepository(db))
    return await service.update_profile(actor["user_id"], body.model_dump(exclude_unset=True))
