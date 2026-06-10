from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_actor, get_rls_db_session
from app.common.dependencies import get_db_session
from app.common.pagination import PaginationRequest
from app.notifications.schemas import NotificationResponse, PaginatedNotificationsResponse
from app.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedNotificationsResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = NotificationService(db)
    result = await svc.list_user_notifications(UUID(actor["user_id"]), pp)
    return PaginatedNotificationsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    svc = NotificationService(db)
    return await svc.get_notification(notification_id, UUID(actor["user_id"]))


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    svc = NotificationService(db)
    return await svc.mark_read(notification_id, UUID(actor["user_id"]))


@router.post("/{notification_id}/dismiss", response_model=NotificationResponse)
async def dismiss_notification(
    notification_id: UUID,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_rls_db_session),
):
    svc = NotificationService(db)
    return await svc.dismiss(notification_id, UUID(actor["user_id"]))
