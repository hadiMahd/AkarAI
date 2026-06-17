"""Repair stuck lead-processing rows by requeueing or recreating lead.created outbox events.

Usage:
    python scripts/repair_stuck_lead_processing.py
    python scripts/repair_stuck_lead_processing.py --apply

Default mode is dry-run and prints what would change.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import select

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.common.database import async_session_factory
from app.common.events import OutboxEvent, publish_outbox_event_in_session
from app.common.rls import apply_rls_context_to_session
from app.leads.models import Lead
from app.leads.schemas import (
    LEAD_PROCESSING_STATUS_PENDING_LEVEL,
    LEAD_PROCESSING_STATUS_PENDING_SPAM,
)


@dataclass
class RepairSummary:
    scanned: int = 0
    requeued_dead_letter: int = 0
    requeued_stale_processing: int = 0
    created_repair_event: int = 0
    skipped_pending_event: int = 0
    skipped_existing_repair: int = 0


def _build_repair_payload(lead: Lead) -> dict[str, str | None]:
    return {
        "lead_id": str(lead.id),
        "tenant_id": str(lead.agency_tenant_id),
        "listing_id": str(lead.listing_id),
        "message": lead.message or "",
        "name": lead.name,
        "email": lead.email,
    }


def _iter_stuck_statuses() -> Iterable[str]:
    yield LEAD_PROCESSING_STATUS_PENDING_SPAM
    yield LEAD_PROCESSING_STATUS_PENDING_LEVEL


async def repair_stuck_lead_processing(*, apply_changes: bool) -> RepairSummary:
    summary = RepairSummary()
    stale_processing_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)

    async with async_session_factory() as session:
        await apply_rls_context_to_session(session, is_platform_admin=True)

        result = await session.execute(
            select(Lead)
            .where(Lead.processing_status.in_(tuple(_iter_stuck_statuses())))
            .order_by(Lead.created_at.asc())
        )
        leads = list(result.scalars().all())
        summary.scanned = len(leads)

        for lead in leads:
            outbox_result = await session.execute(
                select(OutboxEvent)
                .where(
                    OutboxEvent.event_name == "lead.created",
                    OutboxEvent.aggregate_type == "lead",
                    OutboxEvent.aggregate_id == str(lead.id),
                )
                .order_by(OutboxEvent.created_at.desc())
            )
            events = list(outbox_result.scalars().all())

            repair_key = f"repair-lead.created.{lead.id}"
            existing_repair = next((event for event in events if event.idempotency_key == repair_key), None)
            if existing_repair is not None:
                if existing_repair.status in {"pending", "processing", "delivered"}:
                    summary.skipped_existing_repair += 1
                    continue

            reusable = next(
                (
                    event
                    for event in events
                    if event.idempotency_key == f"lead.created.{lead.id}" and event.status == "dead_letter"
                ),
                None,
            )
            if reusable is not None:
                summary.requeued_dead_letter += 1
                if apply_changes:
                    reusable.status = "pending"
                    reusable.retry_count = 0
                    reusable.last_error = None
                    reusable.processed_at = None
                    reusable.available_at = datetime.now(timezone.utc)
                continue

            stale_processing = next(
                (
                    event
                    for event in events
                    if event.idempotency_key == f"lead.created.{lead.id}"
                    and event.status == "processing"
                    and event.updated_at < stale_processing_cutoff
                ),
                None,
            )
            if stale_processing is not None:
                summary.requeued_stale_processing += 1
                if apply_changes:
                    stale_processing.status = "pending"
                    stale_processing.retry_count = 0
                    stale_processing.last_error = None
                    stale_processing.processed_at = None
                    stale_processing.available_at = datetime.now(timezone.utc)
                continue

            active_event = next((event for event in events if event.status in {"pending", "processing"}), None)
            if active_event is not None:
                summary.skipped_pending_event += 1
                continue

            summary.created_repair_event += 1
            if apply_changes:
                await publish_outbox_event_in_session(
                    session,
                    event_name="lead.created",
                    payload=_build_repair_payload(lead),
                    idempotency_key=repair_key,
                    aggregate_type="lead",
                    aggregate_id=str(lead.id),
                )

        if apply_changes:
            await session.commit()
        else:
            await session.rollback()

    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the repair. Without this flag the script runs in dry-run mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = asyncio.run(repair_stuck_lead_processing(apply_changes=args.apply))
    mode = "applied" if args.apply else "dry_run"
    print(
        "mode={mode} scanned={scanned} requeued_dead_letter={requeued_dead_letter} "
        "requeued_stale_processing={requeued_stale_processing} "
        "created_repair_event={created_repair_event} skipped_pending_event={skipped_pending_event} "
        "skipped_existing_repair={skipped_existing_repair}".format(
            mode=mode,
            scanned=summary.scanned,
            requeued_dead_letter=summary.requeued_dead_letter,
            requeued_stale_processing=summary.requeued_stale_processing,
            created_repair_event=summary.created_repair_event,
            skipped_pending_event=summary.skipped_pending_event,
            skipped_existing_repair=summary.skipped_existing_repair,
        )
    )


if __name__ == "__main__":
    main()
