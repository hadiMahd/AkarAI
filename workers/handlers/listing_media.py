"""Listing media processing handler for worker.

Handles:
- listing.image_uploaded: Moderation, quality scoring, derivative generation
- listing.image_moderation_completed: Post-moderation state update
- listing.image_quality_scored: Post-quality scoring state update
"""

from __future__ import annotations

import logging
from decimal import Decimal

import asyncpg
from outbox import NonRetryableEventError

logger = logging.getLogger("worker.listing_media")


async def handle_listing_image_uploaded(
    conn: asyncpg.Connection,
    payload: dict,
    event_id: str | None = None,
) -> None:
    """Process an uploaded listing image: moderation, quality, derivatives."""
    from app.common.config import settings

    listing_id = payload.get("listing_id")
    listing_photo_id = payload.get("listing_photo_id")
    agency_tenant_id = payload.get("agency_tenant_id")
    object_key = payload.get("object_key")
    content_type = payload.get("content_type", "image/jpeg")
    file_size_bytes = payload.get("file_size_bytes", 0)

    if not all([listing_id, listing_photo_id, agency_tenant_id, object_key]):
        raise NonRetryableEventError("listing.image_uploaded payload is missing required fields")

    logger.info(
        "Processing listing image: photo=%s listing=%s tenant=%s",
        listing_photo_id,
        listing_id,
        agency_tenant_id,
    )

    try:
        # Step 1: Run NSFW moderation
        from app.common.media import calculate_blur_score, process_image_for_derivative
        from app.common.storage import (
            download_object,
            generate_derivative_object_key,
            get_media_bucket,
            upload_object,
        )

        bucket = get_media_bucket()
        file_bytes = download_object(bucket, object_key)

        # Run moderation (simplified - in production, use Falconsai model)
        moderation_result = await _run_nsfw_moderation(file_bytes, content_type=content_type)

        if moderation_result["rejected"]:
            async with conn.transaction():
                await _update_photo_status(
                    conn,
                    listing_photo_id,
                    "rejected",
                    moderation_label=moderation_result["label"],
                    moderation_score=moderation_result["score"],
                )
                await _write_audit_log(
                    conn,
                    listing_photo_id,
                    agency_tenant_id,
                    "listing.image_rejected",
                    "rejected",
                    {"reason": moderation_result["label"], "score": moderation_result["score"]},
                    event_id,
                )
            logger.info("Image rejected by moderation: %s", listing_photo_id)
            return

        # Step 2: Calculate quality score
        quality_score = calculate_blur_score(file_bytes)
        blur_detected = quality_score < settings.media_blur_threshold

        # Step 3: Determine status
        new_status = "warning" if blur_detected else "accepted"

        # Step 4: Generate derivative
        derivative_bytes, width, height = process_image_for_derivative(file_bytes)
        derivative_key = generate_derivative_object_key(
            agency_tenant_id, listing_id, listing_photo_id, "optimized"
        )
        upload_object(bucket, derivative_key, derivative_bytes, "image/webp")

        async with conn.transaction():
            await _update_photo_status(
                conn,
                listing_photo_id,
                new_status,
                moderation_label=moderation_result.get("label", "safe"),
                moderation_score=moderation_result["score"],
                quality_score=quality_score,
                width=width,
                height=height,
                content_type=content_type,
                file_size_bytes=file_size_bytes,
            )
            await _create_derivative_record(
                conn,
                listing_photo_id,
                derivative_key,
                width,
                height,
                len(derivative_bytes),
            )
            audit_event = (
                "listing.image_warning" if blur_detected else "listing.image_derivative_created"
            )
            await _write_audit_log(
                conn,
                listing_photo_id,
                agency_tenant_id,
                audit_event,
                new_status,
                {"quality_score": quality_score, "blur_detected": blur_detected},
                event_id,
            )

        logger.info(
            "Image processed: photo=%s status=%s quality_score=%.2f",
            listing_photo_id,
            new_status,
            quality_score,
        )

    except Exception as e:
        logger.exception("Failed to process listing image: %s", listing_photo_id)
        async with conn.transaction():
            await _update_photo_status(conn, listing_photo_id, "failed")
            await _write_audit_log(
                conn,
                listing_photo_id,
                agency_tenant_id,
                "listing.image_processing_failed",
                "failed",
                {"error": str(e)},
                event_id,
            )
        raise


async def _run_nsfw_moderation(file_bytes: bytes, content_type: str | None = None) -> dict:
    from app.common.media_moderation import run_nsfw_moderation

    return await run_nsfw_moderation(file_bytes, content_type=content_type)


async def _update_photo_status(
    conn: asyncpg.Connection,
    photo_id: str,
    status: str,
    *,
    moderation_label: str | None = None,
    moderation_score: float | None = None,
    quality_score: float | None = None,
    width: int | None = None,
    height: int | None = None,
    content_type: str | None = None,
    file_size_bytes: int | None = None,
) -> None:
    """Update photo status and processing fields."""
    update_fields = {"status": status}
    if moderation_label is not None:
        update_fields["moderation_label"] = moderation_label
    if moderation_score is not None:
        update_fields["moderation_score"] = Decimal(str(moderation_score))
    if quality_score is not None:
        update_fields["quality_score"] = Decimal(str(quality_score))
    if width is not None:
        update_fields["width"] = width
    if height is not None:
        update_fields["height"] = height
    if content_type is not None:
        update_fields["content_type"] = content_type
    if file_size_bytes is not None:
        update_fields["file_size_bytes"] = file_size_bytes

    set_clause = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(update_fields))
    query = f"UPDATE listing_photo_metadata SET {set_clause} WHERE id = $1"
    values = [photo_id] + list(update_fields.values())
    await conn.execute(query, *values)


async def _create_derivative_record(
    conn: asyncpg.Connection,
    photo_id: str,
    object_key: str,
    width: int,
    height: int,
    file_size_bytes: int,
) -> None:
    """Create a derivative record in the database."""
    await conn.execute(
        """
        INSERT INTO listing_photo_derivatives
        (id, listing_photo_metadata_id, variant_name, object_key, format, width, height, file_size_bytes, is_public_safe, created_at)
        VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, true, now())
        ON CONFLICT (listing_photo_metadata_id, variant_name) DO UPDATE
        SET object_key = EXCLUDED.object_key,
            format = EXCLUDED.format,
            width = EXCLUDED.width,
            height = EXCLUDED.height,
            file_size_bytes = EXCLUDED.file_size_bytes,
            is_public_safe = EXCLUDED.is_public_safe
        """,
        photo_id,
        "optimized",
        object_key,
        "webp",
        width,
        height,
        file_size_bytes,
    )


async def _write_audit_log(
    conn: asyncpg.Connection,
    photo_id: str,
    tenant_id: str,
    event_name: str,
    result: str,
    details: dict,
    event_id: str | None,
) -> None:
    """Write an audit log entry."""
    import json

    await conn.execute(
        """
        INSERT INTO media_audit_logs
        (id, agency_tenant_id, listing_photo_metadata_id, outbox_event_id, event_name, result, details, created_at)
        VALUES (gen_random_uuid(), $1, $2, $3::uuid, $4, $5, $6, now())
        ON CONFLICT (outbox_event_id, event_name) WHERE outbox_event_id IS NOT NULL DO UPDATE
        SET result = EXCLUDED.result, details = EXCLUDED.details
        """,
        tenant_id,
        photo_id,
        event_id,
        event_name,
        result,
        json.dumps(details),
    )
