from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.domain import LEAD_STATUS_TRANSITIONS, VALID_LEAD_STATUSES, LEAD_STATUS_NEW, LEAD_STATUS_REVIEWED, LEAD_STATUS_CLOSED
from app.common.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.tenant import TenantContext, require_tenant, ensure_tenant_match
from app.common.events import write_domain_event_log
from app.leads.models import Lead, ReviewedLeadRecord
from app.leads.repository import LeadRepository, ReviewedLeadRepository
from app.listings.repository import ListingRepository


class LeadService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._repo = LeadRepository(session, tenant)
        self._review_repo = ReviewedLeadRepository(session, tenant)
        self._listing_repo = ListingRepository(session, tenant)

    async def create_inquiry(self, listing_id: UUID, user_id: UUID, data: dict) -> Lead:
        listing = await self._listing_repo.get_by_id(listing_id)
        if listing is None or listing.status != "active":
            raise NotFoundError(detail="Listing not found or not active")

        lead = Lead(
            agency_tenant_id=listing.agency_tenant_id,
            listing_id=listing_id,
            user_id=user_id,
            status="new",
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            message=data.get("message"),
            source="web",
        )
        lead = await self._repo.create(lead)
        await write_domain_event_log(
            self._session, "lead.created",
            aggregate_type="lead", aggregate_id=str(lead.id),
            agency_tenant_id=lead.agency_tenant_id, actor_user_id=user_id,
            payload={"listing_id": str(listing_id), "email": lead.email, "source": "web"},
        )
        return lead

    async def list_user_inquiries(self, user_id: UUID, pagination: PaginationRequest) -> PaginationResult:
        items, total = await self._repo.list_by_user(
            user_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def list_tenant_leads(self, pagination: PaginationRequest, reviewed: Optional[bool] = None, status: Optional[str] = None) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit,
            reviewed=reviewed, status=status,
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def get_lead(self, lead_id: UUID) -> Lead:
        ctx = require_tenant(self._tenant)
        lead = await self._repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError(detail="Lead not found")
        ensure_tenant_match(self._tenant, lead.agency_tenant_id)
        return lead

    async def update_lead_status(self, lead_id: UUID, new_status: str) -> Lead:
        ctx = require_tenant(self._tenant)
        lead = await self._repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError(detail="Lead not found")
        ensure_tenant_match(self._tenant, lead.agency_tenant_id)

        if new_status not in VALID_LEAD_STATUSES:
            raise ValidationError(detail=f"Invalid lead status: {new_status}")
        allowed = LEAD_STATUS_TRANSITIONS.get(lead.status, [])
        if new_status not in allowed:
            raise ValidationError(
                detail=f"Cannot transition from '{lead.status}' to '{new_status}'"
            )

        lead.status = new_status
        if new_status == LEAD_STATUS_CLOSED:
            lead.closed_at = datetime.now(timezone.utc)
        await self._session.flush()
        await write_domain_event_log(
            self._session, "lead.status_changed",
            aggregate_type="lead", aggregate_id=str(lead.id),
            agency_tenant_id=lead.agency_tenant_id, actor_user_id=ctx.actor_id,
            payload={"status": new_status},
        )
        return lead

    async def review_lead(self, lead_id: UUID, reviewed_by: UUID, data: dict) -> ReviewedLeadRecord:
        ctx = require_tenant(self._tenant)
        lead = await self._repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError(detail="Lead not found")
        ensure_tenant_match(self._tenant, lead.agency_tenant_id)

        if lead.status == LEAD_STATUS_NEW:
            lead.status = LEAD_STATUS_REVIEWED
            await self._session.flush()
            await write_domain_event_log(
                self._session, "lead.reviewed",
                aggregate_type="lead", aggregate_id=str(lead.id),
                agency_tenant_id=lead.agency_tenant_id, actor_user_id=ctx.actor_id,
                payload={"status": "reviewed"},
            )

        record = ReviewedLeadRecord(
            lead_id=lead_id,
            agency_tenant_id=ctx.tenant_id,
            reviewed_by_user_id=reviewed_by,
            outcome=data.get("outcome"),
            notes=data.get("notes"),
        )
        return await self._review_repo.create(record)
