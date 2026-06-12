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

    The helper is fail-closed. Any moderation outage or auth issue rejects the
    image rather than allowing it through.
    """
    from app.common.config import settings

    if not settings.hf_token:
        logger.error(
            "NSFW moderation skipped — HF_TOKEN not configured in Vault "
            "(akarai/ai.hf_token), rejecting upload (fail-closed)"
        )
        return {"rejected": True, "score": 1.0, "label": "moderation_failed"}

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
    except Exception as exc:
        error_msg = str(exc).lower()
        if "401" in error_msg or "unauthorized" in error_msg or "authentication" in error_msg:
            logger.error(
                "NSFW moderation auth failed — check HF_TOKEN in Vault "
                "(akarai/ai.hf_token): %s",
                exc,
            )
        else:
            logger.error("NSFW moderation service error, rejecting upload (fail-closed): %s", exc)
        return {"rejected": True, "score": 1.0, "label": "moderation_failed"}
