from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_tenant_context
from app.common.dependencies import get_db_session
from app.common.exceptions import AppException, RateLimitExceededError
from app.common.pagination import PaginationRequest
from app.common.rate_limit import check_search_rate_limit
from app.common.tenant import TenantContext
from app.search.schemas import (
    AISearchIntentRequest,
    AISearchIntentResponse,
    ConfirmationLogRequest,
    DomainEventLogResponse,
    PaginatedDomainLogsResponse,
    PaginatedSearchLogsResponse,
    SearchLogResponse,
    VoiceSearchResponse,
)
from app.search.service import SearchService

router = APIRouter(prefix="/agency", tags=["Operational Logs"])
public_search_router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/search-logs", response_model=PaginatedSearchLogsResponse)
async def list_search_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = SearchService(db, tenant)
    result = await svc.list_search_logs(pp)
    return PaginatedSearchLogsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@router.get("/domain-logs", response_model=PaginatedDomainLogsResponse)
async def list_domain_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = SearchService(db, tenant)
    result = await svc.list_domain_logs(pp)
    return PaginatedDomainLogsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@public_search_router.post("/intent", response_model=AISearchIntentResponse)
async def extract_search_intent(
    request: Request,
    body: AISearchIntentRequest,
    db: AsyncSession = Depends(get_db_session),
):
    client_ip = request.client.host if request.client else "unknown"
    allowed = await check_search_rate_limit("ai_text", client_ip)
    if not allowed:
        raise RateLimitExceededError(detail="Too many AI-search requests. Please try again later.")

    svc = SearchService(db)
    intent = await svc.extract_search_intent(body.q)
    unclear = intent.unclear_location
    return AISearchIntentResponse(intent=intent, unclear_location=unclear)


@public_search_router.post("/logs/confirmation", status_code=204)
async def log_search_confirmation(
    request: Request,
    body: ConfirmationLogRequest,
    db: AsyncSession = Depends(get_db_session),
):
    svc = SearchService(db)
    await svc._search_repo.create_confirmation_log(
        user_id=None,
        source_mode=body.source_mode,
        filters=body.confirmed_filters.model_dump(exclude_none=True),
        edits=body.edits,
    )


@public_search_router.post("/voice", response_model=VoiceSearchResponse)
async def voice_search(
    request: Request,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    from app.common.config import settings

    client_ip = request.client.host if request.client else "unknown"
    allowed = await check_search_rate_limit("voice", client_ip)
    if not allowed:
        raise RateLimitExceededError(detail="Too many voice search requests. Please try again later.")

    content_type = audio.content_type or "audio/wav"
    allowed_types = [t.strip() for t in settings.voice_allowed_content_types.split(",")]
    if content_type not in allowed_types:
        raise AppException(
            status_code=415,
            detail=f"Unsupported audio format: {content_type}",
            error_code="UNSUPPORTED_AUDIO_FORMAT",
        )

    max_bytes = settings.voice_max_file_size_mb * 1024 * 1024
    audio_bytes = await audio.read(max_bytes + 1)
    if len(audio_bytes) > max_bytes:
        raise AppException(
            status_code=413,
            detail=f"Audio recording exceeds the {settings.voice_max_file_size_mb}MB limit.",
            error_code="AUDIO_FILE_TOO_LARGE",
        )

    svc = SearchService(db)
    return await svc.transcribe_and_extract(audio_bytes, content_type=content_type)
