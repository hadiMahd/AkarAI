from datetime import datetime
from typing import Optional

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
