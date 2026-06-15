import json
import logging
import re
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError, ForbiddenError, ServiceUnavailableError, ValidationError, AppException
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.tenant import TenantContext, require_tenant
from app.search.repository import SearchLogRepository, DomainLogRepository
from app.search.models import SearchLog


def _sanitize_search_log_entry(
    raw_query: Optional[str],
    source_mode: str,
    filters: dict,
    result_count: int,
    provider: Optional[str] = None,
    fallback_reason: Optional[str] = None,
    transcript: Optional[str] = None,
) -> dict:
    # Redact raw_query and transcript: keep only first 200 chars, strip digits that look like phone/id
    def _redact(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        truncated = text[:200]
        return re.sub(r'\b\d{5,}\b', '[REDACTED]', truncated)

    return {
        "source_mode": source_mode,
        "raw_query_redacted": _redact(raw_query),
        "transcript_redacted": _redact(transcript),
        "filters": filters,
        "result_count": result_count,
        "provider": provider,
        "fallback_reason": fallback_reason,
    }


class SearchService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._search_repo = SearchLogRepository(session, tenant)
        self._domain_repo = DomainLogRepository(session, tenant)

    async def log_search_event(self, data: dict) -> SearchLog:
        log = SearchLog(
            user_id=data.get("user_id"),
            agency_tenant_id=data.get("agency_tenant_id"),
            filters=data.get("filters"),
            sort=data.get("sort"),
            result_count=data.get("result_count", 0),
        )
        return await self._search_repo.create(log)

    async def list_search_logs(self, pagination: PaginationRequest) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._search_repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def list_domain_logs(self, pagination: PaginationRequest) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._domain_repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def extract_search_intent(self, q: str) -> "SearchIntent":
        from app.search.schemas import SearchIntent, ConfirmedSearchFilters
        from app.ai.registry import get_chat_provider

        EXTRACTION_PROMPT = (
            "Extract property search filters from the user query as JSON. "
            "Return ONLY valid JSON with keys from: city, location, property_type, listing_purpose, "
            "min_price, max_price, bedrooms, bathrooms, parking, floor, furnishing, "
            "min_area_size, max_area_size. "
            "Use null for missing fields. Example: {\"city\": \"Beirut\", \"bedrooms\": 2}"
        )
        try:
            provider = get_chat_provider()
            response = await provider.chat([
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": q},
            ])
            text = response.get("text", "")
            # Find JSON object in response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                raise ValueError("No JSON in response")
            data = json.loads(match.group())
            # Detect vague location phrases — do NOT expand to city automatically
            from app.search.schemas import UnclearLocationIntent as ULI
            vague_patterns = ["near", "close to", "around", "somewhere", "anywhere", "vicinity"]
            unclear_location = None
            raw_location = data.get("location") or data.get("city", "")
            if raw_location:
                is_vague = any(p in raw_location.lower() for p in vague_patterns)
                if is_vague:
                    unclear_location = ULI(
                        phrase=raw_location,
                        reason="vague_area",
                        suggested_action="select_city",
                    )
                    # Remove vague location from filters — don't auto-apply
                    data.pop("location", None)
                    data.pop("city", None)
            # Note: logging of this intent should happen at the router level
            filters = ConfirmedSearchFilters(**{k: v for k, v in data.items() if v is not None})
            return SearchIntent(
                source_mode="ai_text",
                raw_query=q,
                filters=filters,
                confidence="high",
                provider=response.get("model"),
                unclear_location=unclear_location,
            )
        except Exception as e:
            return SearchIntent(
                source_mode="ai_text",
                raw_query=q,
                filters=ConfirmedSearchFilters(),
                confidence="fallback",
                fallback_reason=str(e)[:200],
            )

    async def transcribe_and_extract(self, audio_bytes: bytes, content_type: str = "audio/wav") -> "VoiceSearchResponse":
        from app.search.schemas import VoiceSearchTranscript, VoiceSearchResponse
        from app.ai.registry import get_stt_provider

        try:
            provider = get_stt_provider()
            transcript_text = await provider.transcribe(audio_bytes, content_type=content_type)
            if not transcript_text or not transcript_text.strip():
                raise ValidationError(
                    detail="We couldn't detect speech in that recording. Try again or type your search instead.",
                    error_code="VOICE_TRANSCRIPTION_EMPTY",
                )
            intent = await self.extract_search_intent(transcript_text)
            intent.source_mode = "voice"
            intent.transcript = transcript_text
            return VoiceSearchResponse(
                transcript=VoiceSearchTranscript(
                    transcript=transcript_text,
                    provider="azure_whisper",
                    confidence="usable",
                ),
                intent=intent,
            )
        except AppException:
            raise
        except Exception as e:
            logging.getLogger(__name__).warning(
                "Voice transcription failed: %s",
                str(e)[:200],
            )
            raise ServiceUnavailableError(
                detail="Voice transcription is unavailable right now. Try again or type your search instead.",
                error_code="VOICE_TRANSCRIPTION_UNAVAILABLE",
            ) from e
