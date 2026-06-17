from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.domain import LEAD_STATUS_TRANSITIONS, VALID_LEAD_STATUSES, LEAD_STATUS_NEW, LEAD_STATUS_REVIEWED, LEAD_STATUS_CLOSED
from app.common.exceptions import AppException, NotFoundError, ForbiddenError, ValidationError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.tenant import TenantContext, require_tenant, ensure_tenant_match
from app.common.events import write_domain_event_log, publish_outbox_event_in_session
from app.common.config import settings
from app.leads.models import Lead, ReviewedLeadRecord, LeadSpamResult, LeadLevelResult
from app.leads.repository import (
    LeadRepository,
    ReviewedLeadRepository,
    LeadSpamResultRepository,
    LeadLevelResultRepository,
)
from app.leads.schemas import (
    LEAD_PROCESSING_STAGE_SPAM,
    LEAD_PROCESSING_STAGE_LEVEL,
    LEAD_PROCESSING_STATUS_PENDING_SPAM,
    LEAD_PROCESSING_STATUS_PENDING_LEVEL,
    LEAD_PROCESSING_STATUS_COMPLETED,
    LEAD_PROCESSING_STATUS_FAILED,
    LEAD_SPAM_LABEL_SPAM,
    LEAD_SPAM_LABEL_NOT_SPAM,
)
from app.listings.repository import ListingRepository
from app.users.repository import UsersRepository
from app.users.service import UsersService


class LeadService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._repo = LeadRepository(session, tenant)
        self._review_repo = ReviewedLeadRepository(session, tenant)
        self._spam_repo = LeadSpamResultRepository(session, tenant)
        self._level_repo = LeadLevelResultRepository(session, tenant)
        self._listing_repo = ListingRepository(session, tenant)

    async def create_inquiry(self, listing_id: UUID, user_id: UUID, data: dict) -> Lead:
        listing = await self._listing_repo.get_by_id(listing_id)
        if listing is None or listing.status != "active":
            raise NotFoundError(detail="Listing not found or not active")

        users_service = UsersService(UsersRepository(self._session))
        user = await users_service.get_user(str(user_id))
        if user is None:
            raise NotFoundError(detail="User not found")

        missing_fields = users_service.get_lead_profile_missing_fields(user)
        if missing_fields:
            raise AppException(
                status_code=422,
                detail="Complete your profile with your name and at least one contact method before sending a lead.",
                error_code="PROFILE_INCOMPLETE_FOR_LEADS",
                extra={"missing_fields": missing_fields},
            )

        message = str(data.get("message") or "").strip()
        if not message:
            raise AppException(
                status_code=422,
                detail="Write a short message before sending a lead.",
                error_code="EMPTY_LEAD_MESSAGE",
            )

        is_empty_message = False

        lead = Lead(
            agency_tenant_id=listing.agency_tenant_id,
            listing_id=listing_id,
            user_id=user_id,
            status="new",
            processing_status=LEAD_PROCESSING_STATUS_PENDING_SPAM if not is_empty_message else LEAD_PROCESSING_STATUS_COMPLETED,
            name=user.name.strip() if user.name else None,
            email=user.email.strip() if user.email else None,
            phone=user.phone.strip() if user.phone else None,
            message=message,
            source="web",
        )
        lead = await self._repo.create(lead)

        # Create pending spam result
        await self._spam_repo.create_pending(lead.id, lead.agency_tenant_id)

        # Handle empty message: mark as spam immediately, skip Hot/Normal
        if settings.lead_processing_empty_message_is_spam and is_empty_message:
            await self._spam_repo.upsert_result(
                lead_id=lead.id,
                tenant_id=lead.agency_tenant_id,
                status=LEAD_PROCESSING_STATUS_COMPLETED,
                label=LEAD_SPAM_LABEL_SPAM,
                score=1.0,
                details={"reason": "empty_message"},
                idempotency_key=f"empty_spam_{lead.id}",
            )
            lead.processing_status = LEAD_PROCESSING_STATUS_COMPLETED
            await self._session.flush()
        else:
            # Create pending level result for non-empty messages
            await self._level_repo.create_pending(lead.id, lead.agency_tenant_id)

            # Emit outbox event for async classification
            idempotency_key = f"lead.created.{lead.id}"
            await publish_outbox_event_in_session(
                self._session,
                event_name="lead.created",
                payload={
                    "lead_id": str(lead.id),
                    "tenant_id": str(lead.agency_tenant_id),
                    "listing_id": str(listing_id),
                    "message": message,
                    "name": lead.name,
                    "email": lead.email,
                },
                idempotency_key=idempotency_key,
                aggregate_type="lead",
                aggregate_id=str(lead.id),
            )

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

    async def list_tenant_leads(
        self,
        pagination: PaginationRequest,
        reviewed: Optional[bool] = None,
        status: Optional[str] = None,
        spam_label: Optional[str] = None,
        processing_status: Optional[str] = None,
    ) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit,
            reviewed=reviewed, status=status,
            spam_label=spam_label, processing_status=processing_status,
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def get_lead(self, lead_id: UUID) -> Lead:
        ctx = require_tenant(self._tenant)
        lead = await self._repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError(detail="Lead not found")
        ensure_tenant_match(self._tenant, lead.agency_tenant_id)
        return lead

    async def read_only_get_lead(self, lead_id: UUID) -> Lead | None:
        """Read-only lookup for the agency assistant."""
        ctx = require_tenant(self._tenant)
        lead = await self._repo.get_by_id(lead_id)
        if lead is None:
            return None
        if lead.agency_tenant_id != ctx.tenant_id:
            return None
        return lead

    async def read_only_list_recent_leads(self, limit: int = 5) -> list[Lead]:
        """Read-only recent leads lookup for the agency assistant."""
        from sqlalchemy import select

        from app.leads.models import Lead

        ctx = require_tenant(self._tenant)
        limit = max(1, min(limit, settings.agency_ai_max_tool_lead_results))
        stmt = (
            select(Lead)
            .where(Lead.agency_tenant_id == ctx.tenant_id)
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def read_only_list_leads_by_date(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 5,
    ) -> list[Lead]:
        """Read-only date-range leads lookup for the agency assistant."""
        from sqlalchemy import select

        from app.leads.models import Lead

        ctx = require_tenant(self._tenant)
        limit = max(1, min(limit, settings.agency_ai_max_tool_lead_results))
        stmt = select(Lead).where(Lead.agency_tenant_id == ctx.tenant_id)
        if date_from is not None:
            stmt = stmt.where(Lead.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Lead.created_at <= date_to)
        stmt = stmt.order_by(Lead.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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

    async def process_spam_callback(
        self,
        lead_id: UUID,
        tenant_id: UUID,
        *,
        status: str,
        label: str | None = None,
        score: float | None = None,
        details: dict | None = None,
        retry_count: int = 0,
        idempotency_key: str | None = None,
    ) -> LeadSpamResult:
        """Idempotent spam classification callback from model service.

        Updates the spam result but never resets review state on the lead.
        """
        lead = await self._repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError(detail="Lead not found")
        if str(lead.agency_tenant_id) != str(tenant_id):
            raise ForbiddenError(detail="Tenant mismatch for lead classification callback")

        # Idempotency check: skip if already processed with same key
        if idempotency_key:
            existing = await self._spam_repo.get_by_idempotency(lead_id, idempotency_key)
            if existing is not None:
                return existing

        result = await self._spam_repo.upsert_result(
            lead_id=lead_id,
            tenant_id=tenant_id,
            status=status,
            label=label,
            score=score,
            details=details,
            retry_count=retry_count,
            idempotency_key=idempotency_key,
        )

        # Update lead processing status — but never touch review state
        if status == LEAD_PROCESSING_STATUS_COMPLETED:
            if label == LEAD_SPAM_LABEL_SPAM:
                # Spam confirmed — processing is fully complete
                lead.processing_status = LEAD_PROCESSING_STATUS_COMPLETED
            else:
                # Not spam — advance to pending_level so frontend keeps polling
                lead.processing_status = LEAD_PROCESSING_STATUS_PENDING_LEVEL
        elif status == LEAD_PROCESSING_STATUS_FAILED:
            lead.processing_status = LEAD_PROCESSING_STATUS_FAILED

        await write_domain_event_log(
            self._session, "lead.processing.spam_result",
            aggregate_type="lead", aggregate_id=str(lead.id),
            agency_tenant_id=lead.agency_tenant_id,
            payload={"label": label, "status": status, "idempotency_key": idempotency_key},
        )
        return result

    async def process_level_callback(
        self,
        lead_id: UUID,
        tenant_id: UUID,
        *,
        status: str,
        level: str | None = None,
        score: float | None = None,
        details: dict | None = None,
        retry_count: int = 0,
        idempotency_key: str | None = None,
    ) -> LeadLevelResult:
        """Idempotent Hot/Normal classification callback from model service.

        Updates the level result but never resets review state on the lead.
        """
        lead = await self._repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError(detail="Lead not found")
        if str(lead.agency_tenant_id) != str(tenant_id):
            raise ForbiddenError(detail="Tenant mismatch for lead classification callback")

        # Idempotency check
        if idempotency_key:
            existing = await self._level_repo.get_by_idempotency(lead_id, idempotency_key)
            if existing is not None:
                return existing

        result = await self._level_repo.upsert_result(
            lead_id=lead_id,
            tenant_id=tenant_id,
            status=status,
            level=level,
            score=score,
            details=details,
            retry_count=retry_count,
            idempotency_key=idempotency_key,
        )

        # Mark processing complete — but never touch review state
        if status == LEAD_PROCESSING_STATUS_COMPLETED:
            lead.processing_status = LEAD_PROCESSING_STATUS_COMPLETED
        elif status == LEAD_PROCESSING_STATUS_FAILED:
            lead.processing_status = LEAD_PROCESSING_STATUS_FAILED

        await write_domain_event_log(
            self._session, "lead.processing.level_result",
            aggregate_type="lead", aggregate_id=str(lead.id),
            agency_tenant_id=lead.agency_tenant_id,
            payload={"level": level, "status": status, "idempotency_key": idempotency_key},
        )
        return result

    async def get_spam_result(self, lead_id: UUID) -> Optional[LeadSpamResult]:
        return await self._spam_repo.get_by_lead(lead_id)

    async def get_level_result(self, lead_id: UUID) -> Optional[LeadLevelResult]:
        return await self._level_repo.get_by_lead(lead_id)
