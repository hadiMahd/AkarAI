from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppException
from app.common.storage import get_rag_bucket, iter_object
from app.auth.dependencies import get_rls_db_session, get_tenant_context
from app.common.tenant import TenantContext
from app.rag.schemas import PaginatedRagDocumentsResponse, RagDocumentRead
from app.rag.service import RagDocumentService

router = APIRouter(prefix="/api/v1/agencies/rag/documents", tags=["RAG Documents"])


@router.post("", response_model=RagDocumentRead, status_code=202)
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


@router.get("", response_model=PaginatedRagDocumentsResponse)
async def list_rag_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagDocumentService(db, tenant)
    return await service.list_documents(page=page, page_size=page_size)


@router.get("/{document_id}", response_model=RagDocumentRead)
async def get_rag_document(
    document_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_rls_db_session),
):
    service = RagDocumentService(db, tenant)
    return await service.get_document(document_id)


@router.get("/{document_id}/download")
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
