"""PII redaction for RAG pipeline outputs.

This module provides a thin wrapper around Presidio that is used exclusively
by the RAG sanitization path.  It is loaded lazily on first use so the
import overhead does not affect startup when PII redaction is disabled.

Layering (matches app/rag/redaction.py callers):
  1. Secret-pattern redaction  — regex, always on  (redaction.py)
  2. PII redaction              — Presidio, toggled  (this module)
  3. Payload bounding           — length caps        (redaction.py)
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# UUID pattern — structural identifiers are never PII content.
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Placeholder replacements for each Presidio entity type.
# Deliberately conservative:
# - URL and DATE_TIME excluded: appear legitimately in policy text, too noisy.
# - US_BANK_NUMBER excluded: UUID hex segments trigger false positives.
_ENTITY_REPLACEMENTS: dict[str, str] = {
    "EMAIL_ADDRESS": "[REDACTED_EMAIL]",
    "PHONE_NUMBER": "[REDACTED_PHONE]",
    "PERSON": "[REDACTED_NAME]",
    "CREDIT_CARD": "[REDACTED_CARD]",
    "IBAN_CODE": "[REDACTED_IBAN]",
    "US_SSN": "[REDACTED_SSN]",
    "IP_ADDRESS": "[REDACTED_IP]",
}

# Entity types to detect.  Ordered by specificity — more specific types first
# reduces false positives when entities overlap.
_ENTITY_TYPES = list(_ENTITY_REPLACEMENTS.keys())

_analyzer = None
_anonymizer = None
_operators: dict | None = None


def _get_engines():
    """Lazily initialise Presidio engines (one-time cost at first call)."""
    global _analyzer, _anonymizer, _operators
    if _analyzer is not None:
        return _analyzer, _anonymizer, _operators

    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        from presidio_anonymizer import AnonymizerEngine
        from presidio_anonymizer.entities import OperatorConfig

        # Use en_core_web_sm (12 MB) instead of the default en_core_web_lg (382 MB).
        # All targeted entities except PERSON are regex-based and unaffected by model size.
        nlp_engine = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }
        ).create_engine()
        _analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        _anonymizer = AnonymizerEngine()
        _operators = {
            entity: OperatorConfig("replace", {"new_value": placeholder})
            for entity, placeholder in _ENTITY_REPLACEMENTS.items()
        }
        logger.info("Presidio PII redaction engines initialised")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Presidio unavailable — PII redaction disabled: %s", exc)
        _analyzer = False  # sentinel: init attempted, unavailable
        _anonymizer = None
        _operators = None

    return _analyzer, _anonymizer, _operators


def _is_enabled() -> bool:
    from app.common.config import settings

    return getattr(settings, "ai_pii_redaction_enabled", True)


def redact_pii_text(text: str) -> str:
    """Return *text* with PII entities replaced by placeholder tokens.

    Falls back to the original string if Presidio is not available or
    PII redaction is disabled, so callers are always safe.
    """
    if not text or not _is_enabled():
        return text
    # Skip UUID strings — they are structural identifiers, not PII content.
    # Without this guard, UUID hex segments trigger US_BANK_NUMBER false positives.
    if _UUID_RE.match(text):
        return text

    analyzer, anonymizer, operators = _get_engines()
    if not analyzer:
        return text

    try:
        results = analyzer.analyze(text=text, language="en", entities=_ENTITY_TYPES)
        if not results:
            return text
        anonymized = anonymizer.anonymize(
            text=text, analyzer_results=results, operators=operators
        )
        return anonymized.text
    except Exception as exc:  # noqa: BLE001
        logger.warning("PII redaction failed, returning original text: %s", exc)
        return text


def redact_pii_payload(obj: Any, *, _depth: int = 0) -> Any:
    """Recursively apply PII redaction to all string values in *obj*.

    Mirrors the structure of ``sanitize_payload`` in ``app.rag.redaction``
    and shares the same depth cap.
    """
    if _depth > 10:
        return obj
    if isinstance(obj, str):
        return redact_pii_text(obj)
    if isinstance(obj, dict):
        return {k: redact_pii_payload(v, _depth=_depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_pii_payload(item, _depth=_depth + 1) for item in obj]
    return obj
