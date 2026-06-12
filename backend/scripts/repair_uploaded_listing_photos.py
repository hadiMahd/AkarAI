"""Requeue listing photos that were left in `uploaded` before worker async dispatch was fixed.

Usage:
    python scripts/repair_uploaded_listing_photos.py

This script scans for listing photos still marked `uploaded`, skips photos that
already have a derivative, and republishes the original `listing.image_uploaded`
outbox event so the worker can finish moderation + derivative generation.
"""

from __future__ import annotations

import asyncio
import os
import sys
from uuid import UUID

from sqlalchemy import select

# Allow running from the backend container root (`/app`).
if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.common.database import async_session_factory
from app.common.events import OutboxEvent, publish_outbox_event_in_session
from app.common.rls import apply_rls_context_to_session
from app.listings.models import ListingPhotoDerivative, ListingPhotoMetadata


async def repair_uploaded_photos() -> int:
    async with async_session_factory() as session:
        await apply_rls_context_to_session(session, is_platform_admin=True)
        result = await session.execute(
            select(ListingPhotoMetadata)
            .where(ListingPhotoMetadata.status == "uploaded")
            .order_by(ListingPhotoMetadata.created_at.asc())
        )
        photos = list(result.scalars().all())

    queued = 0
    skipped = 0

    async with async_session_factory() as session:
        await apply_rls_context_to_session(session, is_platform_admin=True)
        for photo in photos:
            has_derivative = await session.execute(
                select(ListingPhotoDerivative.id).where(
                    ListingPhotoDerivative.listing_photo_metadata_id == photo.id
                ).limit(1)
            )
            if has_derivative.scalar_one_or_none() is not None:
                skipped += 1
                continue

            idempotency_key = f"repair-listing.image_uploaded-{photo.id}"
            existing_event = await session.execute(
                select(OutboxEvent.id).where(OutboxEvent.idempotency_key == idempotency_key)
            )
            if existing_event.scalar_one_or_none() is not None:
                skipped += 1
                continue

            await publish_outbox_event_in_session(
                session,
                "listing.image_uploaded",
                payload={
                    "listing_id": str(photo.listing_id),
                    "listing_photo_id": str(photo.id),
                    "agency_tenant_id": str(photo.agency_tenant_id),
                    "object_key": photo.object_key,
                    "content_type": photo.content_type or "image/jpeg",
                    "file_size_bytes": photo.file_size_bytes or 0,
                    "uploaded_by_user_id": None,
                },
                idempotency_key=idempotency_key,
                aggregate_type="listing_photo",
                aggregate_id=str(photo.id),
            )
            await session.commit()
            queued += 1

    print(f"queued={queued} skipped={skipped} scanned={len(photos)}")
    return queued


def main() -> None:
    asyncio.run(repair_uploaded_photos())


if __name__ == "__main__":
    main()
