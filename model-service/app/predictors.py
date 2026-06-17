"""Two-stage inference: spam classifier → Hot/Normal ranker for non-spam leads.

Stage 1: sklearn Pipeline (TfidfVectorizer + LinearSVC) from spam_pipeline.joblib
          Classes: 0=spam, 1=not_spam (lead)
Stage 2: HuggingFace ModernBERT transformer from level_transformer/
          Classes: 0=normal, 1=hot
"""
from __future__ import annotations

import logging
import math
import os
from typing import Any

from app.config import settings

logger = logging.getLogger("model-service.predictors")

# ── Spam classifier (sklearn Pipeline) ──────────────────────────────────

_spam_pipeline = None
_spam_unavailable = False
_spam_input_columns: list[str] | None = None


def _load_spam_pipeline() -> Any:
    global _spam_pipeline, _spam_unavailable, _spam_input_columns
    if _spam_pipeline is not None or _spam_unavailable:
        return _spam_pipeline

    if not os.path.exists(settings.spam_pipeline_path):
        logger.warning(
            "Spam pipeline not found at %s — using fail-open default (not_spam)",
            settings.spam_pipeline_path,
        )
        _spam_unavailable = True
        return None

    try:
        import joblib
        artifact = joblib.load(settings.spam_pipeline_path)
        if isinstance(artifact, dict):
            columns = artifact.get("input_columns")
            if isinstance(columns, list) and columns:
                _spam_input_columns = [str(column) for column in columns]
            artifact = artifact.get("model")
        _spam_pipeline = artifact
        if _spam_pipeline is None:
            raise ValueError("spam artifact did not contain a usable model")
        logger.info("Spam pipeline loaded (classes=%s)", list(getattr(_spam_pipeline, "classes_", [])))
    except Exception as e:
        logger.warning("Could not load spam pipeline from %s: %s", settings.spam_pipeline_path, e)
        _spam_unavailable = True
    return _spam_pipeline


def _resolve_positive_class_index(classes: Any) -> int:
    if classes is None:
        class_values = []
    else:
        class_values = list(classes)
    if not class_values:
        return 1
    for index, value in enumerate(class_values):
        if str(value) == "1":
            return index
    return min(1, len(class_values) - 1)


def _sigmoid(score: float) -> float:
    bounded = max(min(score, 60.0), -60.0)
    return 1.0 / (1.0 + math.exp(-bounded))


def _predict_not_spam_probability(pipeline: Any, text: str) -> tuple[float, dict[str, float]]:
    from pandas import DataFrame

    classes = getattr(pipeline, "classes_", None)
    positive_index = _resolve_positive_class_index(classes)
    input_columns = _spam_input_columns or ["text"]
    model_input = DataFrame([{input_columns[0]: text}])

    if hasattr(pipeline, "predict_proba"):
        probabilities = pipeline.predict_proba(model_input)[0]
        not_spam_probability = float(probabilities[positive_index])
        spam_probability = 1.0 - not_spam_probability
        return not_spam_probability, {
            "not_spam_probability": not_spam_probability,
            "lead_probability": not_spam_probability,
            "spam_probability": spam_probability,
        }

    if hasattr(pipeline, "decision_function"):
        raw_score = pipeline.decision_function(model_input)
        if isinstance(raw_score, (list, tuple)):
            score = float(raw_score[0])
        else:
            try:
                score = float(raw_score.item())
            except AttributeError:
                score = float(raw_score)

        not_spam_probability = _sigmoid(score)
        return not_spam_probability, {
            "not_spam_probability": not_spam_probability,
            "lead_probability": not_spam_probability,
            "spam_probability": 1.0 - not_spam_probability,
            "score_source": "decision_function",
            "raw_decision_score": score,
        }

    prediction = pipeline.predict(model_input)[0]
    is_not_spam = str(prediction) == "1"
    not_spam_probability = 1.0 if is_not_spam else 0.0
    return not_spam_probability, {
        "not_spam_probability": not_spam_probability,
        "lead_probability": not_spam_probability,
        "spam_probability": 1.0 - not_spam_probability,
        "score_source": "predict_only",
    }


# ── Level ranker (HuggingFace transformer) ──────────────────────────────

_level_model = None
_level_tokenizer = None
_level_unavailable = False


def _load_level_transformer() -> tuple[Any, Any] | tuple[None, None]:
    global _level_model, _level_tokenizer, _level_unavailable
    if _level_model is not None or _level_unavailable:
        return _level_model, _level_tokenizer

    if not os.path.isdir(settings.level_transformer_path):
        logger.warning(
            "Level transformer not found at %s — using fail-open default (normal)",
            settings.level_transformer_path,
        )
        _level_unavailable = True
        return None, None

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        _level_tokenizer = AutoTokenizer.from_pretrained(settings.level_transformer_path)
        _level_model = AutoModelForSequenceClassification.from_pretrained(settings.level_transformer_path)
        logger.info("Level transformer loaded (type=%s)", type(_level_model).__name__)
    except Exception as e:
        logger.warning("Could not load level transformer from %s: %s", settings.level_transformer_path, e)
        _level_unavailable = True
    return _level_model, _level_tokenizer


# ── Public inference interface ──────────────────────────────────────────

def classify_spam(message: str, name: str | None = None, email: str | None = None) -> dict[str, Any]:
    """Classify a lead as spam or not_spam.

    Returns a dict with keys: status, label, score, details.
    Uses fail-open: if model is unavailable, returns not_spam.
    """
    if settings.empty_message_is_spam and not message.strip():
        return {
            "status": "completed",
            "label": "spam",
            "score": 1.0,
            "details": {"reason": "empty_message"},
        }

    pipeline = _load_spam_pipeline()

    if pipeline is None:
        logger.warning("Spam classifier unavailable — failing open to not_spam")
        return {
            "status": "completed",
            "label": "not_spam",
            "score": 0.0,
            "details": {"reason": "model_unavailable_fail_open"},
        }

    try:
        text = f"{name or ''} {email or ''} {message}".strip()
        not_spam_probability, details = _predict_not_spam_probability(pipeline, text)
        spam_score = 1.0 - not_spam_probability
        label = "spam" if spam_score >= settings.spam_threshold else "not_spam"
        return {
            "status": "completed",
            "label": label,
            "score": spam_score,
            "details": details,
        }
    except Exception as e:
        logger.exception("Spam classification failed")
        return {
            "status": "failed",
            "label": None,
            "score": None,
            "details": {"error": str(e)},
        }


def classify_level(message: str, name: str | None = None) -> dict[str, Any]:
    """Classify a non-spam lead as hot or normal.

    Returns a dict with keys: status, level, score, details.
    Uses fail-open: if model is unavailable, returns normal.
    """
    model, tokenizer = _load_level_transformer()

    if model is None or tokenizer is None:
        logger.warning("Level ranker unavailable — failing open to normal")
        return {
            "status": "completed",
            "level": "normal",
            "score": 0.0,
            "details": {"reason": "model_unavailable_fail_open"},
        }

    try:
        import torch

        text = f"{name or ''} {message}".strip()
        inputs = tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze(0)

        # Class 0 = normal, class 1 = hot
        hot_score = float(probs[1].item())
        level = "hot" if hot_score >= 0.5 else "normal"
        return {
            "status": "completed",
            "level": level,
            "score": hot_score,
            "details": {"hot_probability": hot_score, "normal_probability": float(probs[0].item())},
        }
    except Exception as e:
        logger.exception("Level classification failed")
        return {
            "status": "failed",
            "level": None,
            "score": None,
            "details": {"error": str(e)},
        }
