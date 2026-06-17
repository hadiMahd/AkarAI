"""Backfill legacy lead-processing rows into the current async pipeline.

Usage:
    python scripts/backfill_legacy_lead_processing.py
    python scripts/backfill_legacy_lead_processing.py --apply

Default mode is dry-run.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass

from sqlalchemy import select

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.common.config import settings
from app.common.database import async_session_factory
from app.common.events import OutboxEvent, publish_outbox_event_in_session
from app.common.rls import apply_rls_context_to_session
from app.agencies import models as _agency_models  # noqa: F401
from app.leads.models import Lead, LeadLevelResult, LeadSpamResult
from app.listings import models as _listing_models  # noqa: F401
from app.users import models as _user_models  # noqa: F401
from app.leads.schemas import (
    LEAD_PROCESSING_STATUS_COMPLETED,
    LEAD_PROCESSING_STATUS_PENDING,
    LEAD_PROCESSING_STATUS_PENDING_SPAM,
    LEAD_SPAM_LABEL_SPAM,
)


@dataclass
class BackfillSummary:
    scanned: int = 0
    empty_completed: int = 0
    non_empty_queued: int = 0
    spam_rows_created: int = 0
    level_rows_created: int = 0
    outbox_created: int = 0


def _is_empty_message(message: str | None) -> bool:
    return not (message or "").strip()


def _build_payload(lead: Lead) -> dict[str, str | None]:
    return {
        "lead_id": str(lead.id),
        "tenant_id": str(lead.agency_tenant_id),
        "listing_id": str(lead.listing_id),
        "message": lead.message or "",
        "name": lead.name,
        "email": lead.email,
    }


async def backfill_legacy_lead_processing(*, apply_changes: bool) -> BackfillSummary:
    summary = BackfillSummary()

    async with async_session_factory() as session:
        await apply_rls_context_to_session(session, is_platform_admin=True)

        result = await session.execute(
            select(Lead)
            .where(Lead.processing_status == LEAD_PROCESSING_STATUS_PENDING)
            .order_by(Lead.created_at.asc())
        )
        leads = list(result.scalars().all())
        summary.scanned = len(leads)

        for lead in leads:
            spam_result = (
                await session.execute(select(LeadSpamResult).where(LeadSpamResult.lead_id == lead.id))
            ).scalar_one_or_none()
            level_result = (
                await session.execute(select(LeadLevelResult).where(LeadLevelResult.lead_id == lead.id))
            ).scalar_one_or_none()
            outbox_event = (
                await session.execute(
                    select(OutboxEvent).where(OutboxEvent.idempotency_key == f"lead.created.{lead.id}")
                )
            ).scalar_one_or_none()

            if _is_empty_message(lead.message) and settings.lead_processing_empty_message_is_spam:
                summary.empty_completed += 1
                if spam_result is None:
                    summary.spam_rows_created += 1
                    if apply_changes:
                        session.add(
                            LeadSpamResult(
                                lead_id=lead.id,
                                agency_tenant_id=lead.agency_tenant_id,
                                status=LEAD_PROCESSING_STATUS_COMPLETED,
                                label=LEAD_SPAM_LABEL_SPAM,
                                score=1.0,
                                details={"reason": "empty_message_legacy_backfill"},
                                idempotency_key=f"legacy_empty_spam_{lead.id}",
                            )
                        )
                elif apply_changes:
                    spam_result.status = LEAD_PROCESSING_STATUS_COMPLETED
                    spam_result.label = LEAD_SPAM_LABEL_SPAM
                    spam_result.score = 1.0
                    spam_result.details = {"reason": "empty_message_legacy_backfill"}
                    spam_result.idempotency_key = f"legacy_empty_spam_{lead.id}"

                if apply_changes:
                    lead.processing_status = LEAD_PROCESSING_STATUS_COMPLETED
                continue

            summary.non_empty_queued += 1

            if spam_result is None:
                summary.spam_rows_created += 1
                if apply_changes:
                    session.add(
                        LeadSpamResult(
                            lead_id=lead.id,
                            agency_tenant_id=lead.agency_tenant_id,
                            status="pending",
                        )
                    )

            if level_result is None:
                summary.level_rows_created += 1
                if apply_changes:
                    session.add(
                        LeadLevelResult(
                            lead_id=lead.id,
                            agency_tenant_id=lead.agency_tenant_id,
                            status="pending",
                        )
                    )

            if outbox_event is None:
                summary.outbox_created += 1
                if apply_changes:
                    await publish_outbox_event_in_session(
                        session,
                        event_name="lead.created",
                        payload=_build_payload(lead),
                        idempotency_key=f"lead.created.{lead.id}",
                        aggregate_type="lead",
                        aggregate_id=str(lead.id),
                    )

            if apply_changes:
                lead.processing_status = LEAD_PROCESSING_STATUS_PENDING_SPAM

        if apply_changes:
            await session.commit()
        else:
            await session.rollback()

    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply changes instead of running a dry-run.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = asyncio.run(backfill_legacy_lead_processing(apply_changes=args.apply))
    mode = "applied" if args.apply else "dry_run"
    print(
        "mode={mode} scanned={scanned} empty_completed={empty_completed} non_empty_queued={non_empty_queued} "
        "spam_rows_created={spam_rows_created} level_rows_created={level_rows_created} outbox_created={outbox_created}".format(
            mode=mode,
            scanned=summary.scanned,
            empty_completed=summary.empty_completed,
            non_empty_queued=summary.non_empty_queued,
            spam_rows_created=summary.spam_rows_created,
            level_rows_created=summary.level_rows_created,
            outbox_created=summary.outbox_created,
        )
    )


if __name__ == "__main__":
    main()
