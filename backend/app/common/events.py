import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, select, update
from sqlalchemy.dialects.postgresql import UUID

from app.common.database import Base, async_session_factory

# Event status constants
OUTBOX_PENDING = "pending"
OUTBOX_PROCESSING = "processing"
OUTBOX_DELIVERED = "delivered"
OUTBOX_FAILED = "failed"
OUTBOX_DEAD_LETTER = "dead_letter"

INBOX_PROCESSING = "processing"
INBOX_CONSUMED = "consumed"
INBOX_FAILED = "failed"

# Prepared future event names
EVENT_NAMES = [
    "lead.created",
    "viewing.scheduled",
    "viewing.cancelled",
    "rag.document_uploaded",
    "listing.image_uploaded",
    "email.notification_requested",
]


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name = Column(String(128), nullable=False)
    aggregate_type = Column(String(64), nullable=True)
    aggregate_id = Column(String(64), nullable=True)
    idempotency_key = Column(String(128), unique=True, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(16), default=OUTBOX_PENDING, nullable=False)
    available_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)


class InboxEvent(Base):
    __tablename__ = "inbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(128), nullable=False)
    consumer_name = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    status = Column(String(16), default=INBOX_PROCESSING, nullable=False)
    received_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)


async def publish_outbox_event(
    event_name: str,
    payload: dict,
    idempotency_key: str,
    aggregate_type: str | None = None,
    aggregate_id: str | None = None,
) -> OutboxEvent:
    async with async_session_factory() as session:
        event = OutboxEvent(
            event_name=event_name,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event


async def record_inbox_event(
    event_id: str,
    consumer_name: str,
    idempotency_key: str,
) -> InboxEvent:
    async with async_session_factory() as session:
        inbox = InboxEvent(
            event_id=event_id,
            consumer_name=consumer_name,
            idempotency_key=idempotency_key,
        )
        session.add(inbox)
        await session.commit()
        await session.refresh(inbox)
        return inbox
