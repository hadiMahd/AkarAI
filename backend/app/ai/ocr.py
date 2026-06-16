"""OCR spec extraction helpers — converts raw OCR text into structured
listing field candidates.

The flow is intentionally simple and defensive: heuristics over a single
extracted text body. This is not a replacement for full structured form
filler, but it gives the agency admin a reviewable starting point inside
the listing form.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from app.ai.registry import get_chat_provider


_AREA_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(sqm|sq\.?\s?m|m2|m\^2|sqft|square feet|sq\.?\s?ft)", re.IGNORECASE)
_BEDROOMS_RE = re.compile(r"(\d+)\s*(?:bed(?:room)?s?|br|beds)\b", re.IGNORECASE)
_BATHROOMS_RE = re.compile(r"(\d+)\s*(?:bath(?:room)?s?|ba)\b", re.IGNORECASE)
_PARKING_RE = re.compile(r"(\d+)\s*(?:parking|car\s*space|garage)\b", re.IGNORECASE)
_FLOOR_RE = re.compile(r"(?:floor|level)\s*(\d+)", re.IGNORECASE)

_PROPERTY_TYPE_HINTS = {
    "apartment": ("apartment", "apt", "flat"),
    "villa": ("villa",),
    "house": ("house", "townhouse", "duplex"),
    "office": ("office",),
    "studio": ("studio",),
    "shop": ("shop", "store", "retail"),
}

_PURPOSE_HINTS = {
    "rent": ("rent", "for rent", "rental"),
    "sale": ("sale", "for sale", "buy"),
}

_FURNISHING_HINTS = {
    "furnished": ("furnished",),
    "unfurnished": ("unfurnished", "not furnished"),
    "semi-furnished": ("semi furnished", "semi-furnished", "partially furnished"),
}

_LLM_CONTROLLED_FIELDS = (
    "property_type",
    "listing_purpose",
    "bedrooms",
    "bathrooms",
    "parking",
    "floor",
    "area_size",
    "area_unit",
    "furnishing",
    "address",
    "city",
    "location_text",
)


def _coerce_int(value: str | None) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_decimal(value: str | None) -> Optional[Decimal]:
    if not value:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _first_match(re_obj: re.Pattern[str], text: str) -> Optional[str]:
    match = re_obj.search(text)
    return match.group(1) if match else None


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    lowered = haystack.lower()
    return any(needle in lowered for needle in needles)


def extract_listing_specs(text: str) -> dict[str, Any]:
    """Convert raw OCR text into reviewable listing field candidates.

    Returns a dict with the same shape as ExtractedListingSpecs plus a
    ``field_confidence`` and ``source_snippets`` map. The caller decides
    which fields to apply to the listing form; this function never
    mutates any persistent state.
    """
    if not text:
        return {
            "raw_text_excerpt": "",
            "field_confidence": {},
            "source_snippets": {},
        }

    cleaned = " ".join(text.split())
    excerpt = cleaned[:1500]

    field_confidence: dict[str, str] = {}
    source_snippets: dict[str, str] = {}

    specs: dict[str, Any] = {
        "raw_text_excerpt": excerpt,
    }

    if area_match := _AREA_SIZE_RE.search(cleaned):
        specs["area_size"] = _coerce_decimal(area_match.group(1))
        specs["area_unit"] = area_match.group(2).lower().replace(".", "").replace(" ", "").replace("^", "")
        if specs["area_unit"] in ("sqft", "sqft."):
            specs["area_unit"] = "sqft"
        elif specs["area_unit"] in ("sqm",):
            specs["area_unit"] = "sqm"
        elif specs["area_unit"] in ("m2", "m^2"):
            specs["area_unit"] = "sqm"
        field_confidence["area_size"] = "high" if specs["area_size"] else "low"
        source_snippets["area_size"] = area_match.group(0)

    bedrooms_value = _coerce_int(_first_match(_BEDROOMS_RE, cleaned))
    if bedrooms_value is not None:
        specs["bedrooms"] = bedrooms_value
        field_confidence["bedrooms"] = "high"
        source_snippets["bedrooms"] = _BEDROOMS_RE.search(cleaned).group(0)  # type: ignore[union-attr]

    bathrooms_value = _coerce_int(_first_match(_BATHROOMS_RE, cleaned))
    if bathrooms_value is not None:
        specs["bathrooms"] = bathrooms_value
        field_confidence["bathrooms"] = "high"
        source_snippets["bathrooms"] = _BATHROOMS_RE.search(cleaned).group(0)  # type: ignore[union-attr]

    parking_value = _coerce_int(_first_match(_PARKING_RE, cleaned))
    if parking_value is not None:
        specs["parking"] = parking_value
        field_confidence["parking"] = "high"
        source_snippets["parking"] = _PARKING_RE.search(cleaned).group(0)  # type: ignore[union-attr]

    floor_value = _coerce_int(_first_match(_FLOOR_RE, cleaned))
    if floor_value is not None:
        specs["floor"] = floor_value
        field_confidence["floor"] = "high"
        source_snippets["floor"] = _FLOOR_RE.search(cleaned).group(0)  # type: ignore[union-attr]

    for value, hints in _PROPERTY_TYPE_HINTS.items():
        if _contains_any(cleaned, hints):
            specs["property_type"] = value
            field_confidence["property_type"] = "medium"
            break

    for value, hints in _PURPOSE_HINTS.items():
        if _contains_any(cleaned, hints):
            specs["listing_purpose"] = value
            field_confidence["listing_purpose"] = "medium"
            break

    for value, hints in _FURNISHING_HINTS.items():
        if _contains_any(cleaned, hints):
            specs["furnishing"] = value
            field_confidence["furnishing"] = "medium"
            break

    city_match = re.search(r"(?:city|in|at)\s+([A-Z][a-zA-Z]+)", cleaned)
    if city_match:
        specs["city"] = city_match.group(1)
        field_confidence["city"] = "low"
        source_snippets["city"] = city_match.group(0)

    address_match = re.search(
        r"(?:address|street|location)\s*[:\-]?\s*([A-Za-z0-9 ,.'-]{3,80})",
        cleaned,
    )
    if address_match:
        specs["address"] = address_match.group(1).strip().rstrip(",.")
        field_confidence["address"] = "low"
        source_snippets["address"] = address_match.group(0)

    return {
        **specs,
        "field_confidence": field_confidence,
        "source_snippets": source_snippets,
    }


async def extract_listing_specs_via_llm(text: str) -> dict[str, Any]:
    """Normalize OCR text into the listing form schema with an LLM fallback.

    The model maps noisy or handwritten OCR into the app's structured
    listing fields, then we merge in the deterministic heuristic extractor
    as a safety net for missing fields.
    """
    heuristic = extract_listing_specs(text)
    if not text or not text.strip():
        return heuristic

    prompt = [
        {
            "role": "system",
            "content": (
                "You normalize OCR text for a real-estate listing form. "
                "Return compact JSON only. Use these keys: "
                "property_type, listing_purpose, bedrooms, bathrooms, parking, floor, "
                "area_size, area_unit, furnishing, address, city, location_text, "
                "raw_text_excerpt, field_confidence, source_snippets. "
                "Use null for unknown values. Choose controlled values: "
                "property_type in apartment, villa, house, office, studio, shop; "
                "listing_purpose in rent, sale; area_unit in sqm or sqft; "
                "furnishing in furnished, unfurnished, semi-furnished. "
                "Keep raw_text_excerpt short and exact. "
                "Use source_snippets as short exact quotes from the OCR text when possible. "
                "Do not add commentary."
            ),
        },
        {
            "role": "user",
            "content": (
                "Normalize this OCR text into the listing form schema:\n\n"
                f"{text[:8000]}"
            ),
        },
    ]

    try:
        provider = get_chat_provider()
        response = await provider.chat(prompt, temperature=0)
        parsed = _parse_json_object(response.get("text") or "")
    except Exception:
        return heuristic

    merged = dict(heuristic)
    for field in _LLM_CONTROLLED_FIELDS:
        value = parsed.get(field)
        if value is None:
            continue
        if field in {"bedrooms", "bathrooms", "parking", "floor"}:
            normalized = _coerce_int(str(value))
            if normalized is not None:
                merged[field] = normalized
            continue
        if field == "area_size":
            normalized = _coerce_decimal(str(value))
            if normalized is not None:
                merged[field] = normalized
            continue
        if field == "area_unit":
            unit = str(value).strip().lower().replace(".", "").replace(" ", "")
            if unit in {"sqm", "m2", "m^2"}:
                merged[field] = "sqm"
            elif unit in {"sqft", "sqft"}:
                merged[field] = "sqft"
            continue
        merged[field] = str(value).strip()

    llm_confidence = parsed.get("field_confidence")
    if isinstance(llm_confidence, dict):
        merged_confidence = dict(heuristic.get("field_confidence") or {})
        merged_confidence.update({str(k): str(v) for k, v in llm_confidence.items() if str(k).strip()})
        merged["field_confidence"] = merged_confidence
    llm_snippets = parsed.get("source_snippets")
    if isinstance(llm_snippets, dict):
        merged_snippets = dict(heuristic.get("source_snippets") or {})
        merged_snippets.update({str(k): str(v) for k, v in llm_snippets.items() if str(k).strip()})
        merged["source_snippets"] = merged_snippets

    excerpt = str(parsed.get("raw_text_excerpt") or heuristic.get("raw_text_excerpt") or "").strip()
    merged["raw_text_excerpt"] = excerpt[:1500]
    return merged


def _parse_json_object(content: str) -> dict[str, Any]:
    if not content.strip():
        return {}
    try:
        value = json.loads(content)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return {}
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
