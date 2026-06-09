import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.common.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    property_type = Column(String(64), nullable=True)
    listing_purpose = Column(String(32), nullable=True)
    price = Column(Numeric(14, 2), nullable=True)
    currency = Column(String(8), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    area_size = Column(Numeric(12, 2), nullable=True)
    area_unit = Column(String(8), nullable=True)
    furnishing = Column(String(32), nullable=True)
    location_text = Column(String(512), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(128), nullable=True)
    country = Column(String(128), nullable=True)
    status = Column(String(16), default="inactive", nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)


class ListingPhotoMetadata(Base):
    __tablename__ = "listing_photo_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    object_key = Column(String(512), nullable=False)
    caption = Column(String(512), nullable=True)
    alt_text = Column(String(512), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    status = Column(String(16), default="pending_upload", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SavedListing(Base):
    __tablename__ = "saved_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class ComparisonSession(Base):
    __tablename__ = "comparison_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class ComparisonItem(Base):
    __tablename__ = "comparison_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comparison_session_id = Column(UUID(as_uuid=True), ForeignKey("comparison_sessions.id", ondelete="CASCADE"), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
