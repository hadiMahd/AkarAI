"""Listing media processing handler shim for backend integration tests.

This mirrors the worker runtime handler closely enough for backend-side tests
to import and exercise the processing flow without depending on the separate
worker image layout.
"""

from __future__ import annotations

import logging

import asyncpg

logger = logging.getLogger("worker.listing_media")


async def handle_listing_image_uploaded(
    conn: asyncpg.Connection,
    payload: dict,
    event_id: str | None = None,
) -> None:
    from app.common.config import settings
    from app.common.media import calculate_blur_score, process_image_for_derivative
    from app.common.storage import (
        download_object,
        generate_derivative_object_key,
        get_media_bucket,
        upload_object,
    )

    listing_id = payload.get("listing_id")
    listing_photo_id = payload.get("listing_photo_id")
    agency_tenant_id = payload.get("agency_tenant_id")
    object_key = payload.get("object_key")
    content_type = payload.get("content_type", "image/jpeg")
    file_size_bytes = payload.get("file_size_bytes", 0)

    if not all([listing_id, listing_photo_id, agency_tenant_id, object_key]):
        logger.error("Missing required fields in image_uploaded payload: %s", payload)
        return

    try:
        bucket = get_media_bucket()
        file_bytes = download_object(bucket, object_key)
        moderation_result = await _run_nsfw_moderation(file_bytes, content_type=content_type)

        if moderation_result["rejected"]:
            await _update_photo_status(
                conn,
                listing_photo_id,
                "rejected",
                moderation_label="nsfw",
                moderation_score=moderation_result["score"],
            )
            await _write_audit_log(
                conn,
                listing_photo_id,
                agency_tenant_id,
                "listing.image_rejected",
                "rejected",
                {"reason": "nsfw", "score": moderation_result["score"]},
            )
            return

        quality_score = calculate_blur_score(file_bytes)
        blur_detected = quality_score < settings.media_blur_threshold
        new_status = "warning" if blur_detected else "accepted"
        derivative_bytes, width, height = process_image_for_derivative(file_bytes)
        derivative_key = generate_derivative_object_key(
            agency_tenant_id, listing_id, listing_photo_id, "optimized"
        )
        upload_object(bucket, derivative_key, derivative_bytes, "image/webp")

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

        audit_event = "listing.image_warning" if blur_detected else "listing.image_derivative_created"
        await _write_audit_log(
            conn,
            listing_photo_id,
            agency_tenant_id,
            audit_event,
            new_status,
            {"quality_score": quality_score, "blur_detected": blur_detected},
        )
    except Exception as e:
        logger.exception("Failed to process listing image: %s", listing_photo_id)
        await _update_photo_status(conn, listing_photo_id, "failed")
        await _write_audit_log(
            conn,
            listing_photo_id,
            agency_tenant_id,
            "listing.image_rejected",
            "failed",
            {"error": str(e)},
        )


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
    update_fields = {"status": status}
    if moderation_label is not None:
        update_fields["moderation_label"] = moderation_label
    if moderation_score is not None:
        update_fields["moderation_score"] = moderation_score
    if quality_score is not None:
        update_fields["quality_score"] = quality_score
    if width is not None:
        update_fields["width"] = width
    if height is not None:
        update_fields["height"] = height
    if content_type is not None:
        update_fields["content_type"] = content_type
    if file_size_bytes is not None:
        update_fields["file_size_bytes"] = file_size_bytes

    set_clause = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(update_fields.keys()))
    values = [photo_id] + list(update_fields.values())

    await conn.execute(
        f"UPDATE listing_photo_metadata SET {set_clause}, updated_at = NOW() WHERE id = $1",
        *values,
    )


async def _create_derivative_record(
    conn: asyncpg.Connection,
    photo_id: str,
    object_key: str,
    width: int,
    height: int,
    file_size_bytes: int,
) -> None:
    await conn.execute(
        """
        INSERT INTO listing_photo_derivatives
            (id, listing_photo_metadata_id, object_key, width, height, file_size_bytes, format, created_at)
        VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, 'webp', NOW())
        """,
        photo_id,
        object_key,
        width,
        height,
        file_size_bytes,
    )


async def _write_audit_log(
    conn: asyncpg.Connection,
    photo_id: str,
    agency_tenant_id: str,
    event_name: str,
    result: str,
    details: dict,
) -> None:
    await conn.execute(
        """
        INSERT INTO media_audit_logs
            (id, event_name, agency_tenant_id, listing_photo_metadata_id, result, details, created_at)
        VALUES (gen_random_uuid(), $1, $2, $3, $4, $5::jsonb, NOW())
        """,
        event_name,
        agency_tenant_id,
        photo_id,
        result,
        details,
    )
