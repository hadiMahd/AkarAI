from __future__ import annotations

import re
from typing import Any

from app.ai.pii_redaction import redact_pii_text, redact_pii_payload

# Patterns that look like real secret values, not just the word "token" in prose.
_REDACT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Authorization: Bearer <token> or just Bearer <token>
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [REDACTED]"),
    # JWT-like: three base64url segments where the first two start with eyJ
    (
        re.compile(r"eyJ[A-Za-z0-9\-_]{4,}\.eyJ[A-Za-z0-9\-_]{4,}\.[A-Za-z0-9\-_]+"),
        "[REDACTED_JWT]",
    ),
    # Common provider API key formats: sk-xxx, sk_xxx (OpenAI, Anthropic style)
    (re.compile(r"\bsk[-_][a-zA-Z0-9]{20,}\b"), "[REDACTED_KEY]"),
    # api_key / apikey / api-key assignment: key=<long value>
    (
        re.compile(r"(?i)(api[_\- ]?key\s*[:=]\s*)['\"]?[A-Za-z0-9\-_\.]{16,}['\"]?"),
        r"\1[REDACTED]",
    ),
    # password / passwd / secret / private_key assignment
    (
        re.compile(
            r"(?i)((?:password|passwd|secret|private[_\-]?key)\s*[:=]\s*)['\"]?\S{8,}['\"]?"
        ),
        r"\1[REDACTED]",
    ),
    # System/developer prompt leakage terms that should not appear in stored answers
    (
        re.compile(
            r"(?i)\b(system\s+prompt|developer\s+prompt|hidden\s+prompt|internal\s+instructions)\b"
        ),
        "[BLOCKED_TERM]",
    ),
]

# Maximum character length for stored evidence previews (defense-in-depth on top of retrieval.py limits).
_MAX_EVIDENCE_PREVIEW_CHARS = 500
_MAX_PARENT_PAGE_TEXT_CHARS = 1000
_MAX_LEAD_MESSAGE_CHARS = 2000
_MAX_LEAD_DETAILS_CHARS = 1000


def redact_text(text: str) -> str:
    """Layer 1 (secret patterns) + Layer 2 (PII) redaction for a single string."""
    # Layer 1: regex secret patterns
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    # Layer 2: PII (Presidio) — runs after secrets so no secret leaks into PII output
    text = redact_pii_text(text)
    return text


def sanitize_payload(obj: Any, *, _depth: int = 0) -> Any:
    """Recursively apply secret-pattern + PII redaction to all strings in a payload.

    Stops recursion at depth 10 to guard against pathological inputs.
    """
    if _depth > 10:
        return obj
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: sanitize_payload(v, _depth=_depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_payload(item, _depth=_depth + 1) for item in obj]
    return obj


def sanitize_answer_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a RagPolicyAnswer payload dict before DB or cache persistence.

    - Redacts secret patterns from all string values.
    - Caps evidence text_preview and parent_page_text lengths.
    - Strips raw provider content from the debug section.
    """
    sanitized = sanitize_payload(payload)

    # Cap evidence preview lengths even after redaction.
    evidence = sanitized.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                preview = item.get("text_preview")
                if isinstance(preview, str) and len(preview) > _MAX_EVIDENCE_PREVIEW_CHARS:
                    item["text_preview"] = preview[:_MAX_EVIDENCE_PREVIEW_CHARS] + "…"
                page_text = item.get("parent_page_text")
                if isinstance(page_text, str) and len(page_text) > _MAX_PARENT_PAGE_TEXT_CHARS:
                    item["parent_page_text"] = page_text[:_MAX_PARENT_PAGE_TEXT_CHARS] + "…"

    # Strip debug fields that could carry raw provider content.
    debug = sanitized.get("debug")
    if isinstance(debug, dict):
        blocked_reason = debug.get("guardrail_blocked_reason")
        if isinstance(blocked_reason, str) and len(blocked_reason) > 120:
            debug["guardrail_blocked_reason"] = blocked_reason[:120]

    return sanitized


def redact_lead_payload(payload: dict) -> dict:
    """Redact PII and secrets from lead-processing payloads before logging or storage."""
    sanitized = sanitize_payload(payload)

    message = sanitized.get("message")
    if isinstance(message, str) and len(message) > _MAX_LEAD_MESSAGE_CHARS:
        sanitized["message"] = message[:_MAX_LEAD_MESSAGE_CHARS] + "…"

    details = sanitized.get("details")
    if isinstance(details, dict):
        for key in list(details.keys()):
            value = details.get(key)
            if isinstance(value, str) and len(value) > _MAX_LEAD_DETAILS_CHARS:
                details[key] = value[:_MAX_LEAD_DETAILS_CHARS] + "…"

    return sanitized
