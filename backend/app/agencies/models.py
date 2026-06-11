import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.common.database import Base


class AgencyTenant(Base):
    __tablename__ = "agency_tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(128), unique=True, nullable=False)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AgencyEmployeeMembership(Base):
    __tablename__ = "agency_employee_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(16), nullable=False, default="active")
    display_name = Column(String(255), nullable=True)
    work_email = Column(String(255), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deactivation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgencyProfile(Base):
    __tablename__ = "agency_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id"), nullable=False)
    display_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    website_url = Column(String(512), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(128), nullable=True)
    country = Column(String(128), nullable=True)
    status = Column(String(16), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
