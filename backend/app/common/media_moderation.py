"""Shared NSFW moderation helpers for listing photo flows."""

from __future__ import annotations

import logging
import os
import tempfile

logger = logging.getLogger("app.media_moderation")


def _suffix_for_content_type(content_type: str | None) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    return mapping.get((content_type or "").lower(), ".jpg")


async def run_nsfw_moderation(file_bytes: bytes, content_type: str | None = None) -> dict:
    """Run NSFW moderation using the configured Hugging Face model.

    Returns a dict with:
    - rejected: bool
    - score: float
    - label: str

    Provider failures raise so the outbox can retry them. A rejection is only
    returned when the provider actually classifies the image as NSFW.
    """
    from app.common.config import settings

    if not settings.hf_token:
        raise RuntimeError("NSFW moderation is not configured")

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(api_key=settings.hf_token)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=_suffix_for_content_type(content_type),
                delete=False,
            ) as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name

            result = client.image_classification(
                temp_path,
                model="Falconsai/nsfw_image_detection",
            )
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    logger.warning("Failed to remove temporary moderation file: %s", temp_path)

        nsfw_score = 0.0
        for item in result:
            label = getattr(item, "label", None)
            score = getattr(item, "score", None)
            if label is None and isinstance(item, dict):
                label = item.get("label")
                score = item.get("score")

            if label == "nsfw":
                nsfw_score = float(score or 0.0)
                break

        rejected = nsfw_score >= settings.media_nsfw_threshold
        return {
            "rejected": rejected,
            "score": float(nsfw_score),
            "label": "nsfw" if rejected else "safe",
        }
    except Exception:
        logger.exception("NSFW moderation service failed")
        raise
