from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_rls_db_session, get_tenant_context, require_role
from app.common.exceptions import AppException
from app.common.storage import get_rag_bucket, iter_object
from app.common.tenant import TenantContext
from app.rag.schemas import (
    PaginatedRagChatThreadsResponse,
    PaginatedRagDocumentsResponse,
    PaginatedRagRetrievalLogsResponse,
    RagChatMessageCreateRequest,
    RagChatSendMessageResponse,
    RagChatThreadCreateRequest,
    RagChatThreadDetailResponse,
    RagDocumentRead,
    RagPolicyAnswer,
    RagRetrievalLogFilter,
    RagRetrievalQueryRequest,
)
from app.rag.service import RagChatService, RagDocumentService, RagRetrievalService

# ── Document endpoints ──────────────────────────────────────────

doc_router = APIRouter(prefix="/api/v1/agencies/rag/documents", tags=["RAG Documents"])


@doc_router.post("", response_model=RagDocumentRead, status_code=202)
async def upload_rag_document(
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    file_bytes = await file.read()
    filename = file.filename or "document.pdf"
    content_type = file.content_type
    service = RagDocumentService(db, tenant)
    return await service.upload_document(file_bytes=file_bytes, filename=filename, content_type=content_type)


@doc_router.post("/{document_id}/replace", response_model=RagDocumentRead, status_code=202)
async def replace_rag_document(
    document_id: UUID,
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    file_bytes = await file.read()
    filename = file.filename or "document.pdf"
    content_type = file.content_type
    service = RagDocumentService(db, tenant)
    return await service.replace_document(
        document_id=document_id,
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )


@doc_router.get("", response_model=PaginatedRagDocumentsResponse)
async def list_rag_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagDocumentService(db, tenant)
    return await service.list_documents(page=page, page_size=page_size)


@doc_router.get("/{document_id}", response_model=RagDocumentRead)
async def get_rag_document(
    document_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagDocumentService(db, tenant)
    return await service.get_document(document_id)


@doc_router.get("/{document_id}/download")
async def download_rag_document(
    document_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagDocumentService(db, tenant)
    document = await service.get_document(document_id)
    headers = {
        "Content-Disposition": f'inline; filename="{document.filename}"',
    }
    try:
        return StreamingResponse(
            iter_object(get_rag_bucket(), document.blob_path),
            media_type="application/pdf",
            headers=headers,
        )
    except Exception as exc:
        raise AppException(status_code=404, detail="Document file not found in storage") from exc


# ── Retrieval endpoints ─────────────────────────────────────────

retrieval_router = APIRouter(prefix="/api/v1/agencies/rag", tags=["RAG Retrieval"])

chat_router = APIRouter(prefix="/api/v1/agencies/rag/chat", tags=["RAG Chat"])


@retrieval_router.post("/query", response_model=RagPolicyAnswer)
async def query_policy_documents(
    request: RagRetrievalQueryRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagRetrievalService(db, tenant)
    return await service.answer_policy_query(request)


@retrieval_router.get("/retrieval-logs", response_model=PaginatedRagRetrievalLogsResponse)
async def list_retrieval_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor_role: str | None = Query(None),
    confidence_status: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
    _: dict = Depends(require_role("agency_admin")),
):
    filters = RagRetrievalLogFilter(
        actor_role=actor_role,
        confidence_status=confidence_status,
        date_from=date_from,
        date_to=date_to,
    )
    service = RagRetrievalService(db, tenant)
    return await service.list_retrieval_logs(page=page, page_size=page_size, filters=filters)


@chat_router.get("/threads", response_model=PaginatedRagChatThreadsResponse)
async def list_rag_chat_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagChatService(db, tenant)
    return await service.list_threads(page=page, page_size=page_size)


@chat_router.post("/threads", response_model=RagChatThreadDetailResponse, status_code=201)
async def create_rag_chat_thread(
    request: RagChatThreadCreateRequest | None = None,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagChatService(db, tenant)
    thread = await service.create_thread(request or RagChatThreadCreateRequest())
    return RagChatThreadDetailResponse(thread=thread, messages=[])


@chat_router.get("/threads/{thread_id}", response_model=RagChatThreadDetailResponse)
async def get_rag_chat_thread(
    thread_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagChatService(db, tenant)
    return await service.get_thread(thread_id)


@chat_router.post("/threads/{thread_id}/messages", response_model=RagChatSendMessageResponse)
async def send_rag_chat_message(
    thread_id: UUID,
    request: RagChatMessageCreateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagChatService(db, tenant)
    return await service.send_message(thread_id, request)
