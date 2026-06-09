from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class NotificationPayload(BaseModel):
    recipient_email: Optional[str] = None
    recipient_user_id: Optional[str] = None
    template_key: str
    template_data: dict = {}
    channel: str = "email"


class EmailEventPayload(BaseModel):
    event_name: str = "email.notification_requested"
    to_email: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    template_key: Optional[str] = None
    notification_id: Optional[str] = None


class NotificationResponse(BaseModel):
    id: UUID
    recipient_user_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    channel: str
    template_key: Optional[str] = None
    payload: Optional[dict] = None
    status: str
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedNotificationsResponse(BaseModel):
    items: list[NotificationResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool
