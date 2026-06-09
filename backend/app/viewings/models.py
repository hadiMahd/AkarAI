from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import DateTime

from app.common.database import Base


class ListingViewingSlot(Base):
    __tablename__ = "listing_viewing_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    capacity = Column(Integer, default=1, nullable=False)
    reserved_count = Column(Integer, default=0, nullable=False)
    status = Column(String(16), default="active", nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ScheduledViewing(Base):
    __tablename__ = "scheduled_viewings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    viewing_slot_id = Column(UUID(as_uuid=True), ForeignKey("listing_viewing_slots.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), default="scheduled", nullable=False)
    scheduled_start_at = Column(DateTime(timezone=True), nullable=False)
    scheduled_end_at = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ScheduledViewingStatusHistory(Base):
    __tablename__ = "scheduled_viewing_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scheduled_viewing_id = Column(UUID(as_uuid=True), ForeignKey("scheduled_viewings.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    changed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
