from hashlib import sha256
from uuid import UUID, uuid4

from app.common.exceptions import AppException, ForbiddenError, NotFoundError
from app.common.pagination import PaginationRequest
from app.common.config import settings
from app.common.storage import delete_object, ensure_bucket_exists, get_rag_bucket, upload_object
from app.common.tenant import TenantContext, require_tenant
from app.rag.models import RagDocument
from app.rag.repository import RagRepository
from app.rag.schemas import RagDocumentRead, PaginatedRagDocumentsResponse
from app.common.events import publish_outbox_event_in_session, write_domain_event_log


class RagDocumentService:
    def __init__(self, session, tenant: TenantContext | None = None):
        self._session = session
        self._tenant = tenant
        self._repo = RagRepository(session)

    async def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> RagDocumentRead:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot upload RAG documents")

        safe_filename = _sanitize_filename(filename)
        _validate_pdf_upload(file_bytes, content_type, safe_filename)
        try:
            _extract_text_from_pdf(file_bytes)  # reject unreadable/scanned PDFs before accepting
        except AppException:
            raise
        except Exception as exc:
            raise AppException(
                status_code=400,
                detail="Uploaded PDF does not contain extractable text",
            ) from exc

        document_id = uuid4()
        bucket = get_rag_bucket()
        ensure_bucket_exists(bucket)
        object_key = _build_rag_object_key(ctx.tenant_id, document_id, safe_filename)

        try:
            upload_object(bucket, object_key, file_bytes, "application/pdf")
        except Exception as exc:
            raise AppException(status_code=503, detail=f"Failed to store document: {exc}") from exc

        document = RagDocument(
            tenant_id=ctx.tenant_id,
            filename=safe_filename,
            status="pending",
            blob_path=object_key,
        )

        try:
            document = await self._repo.create_document(document)

            await publish_outbox_event_in_session(
                self._session,
                event_name="rag.document_uploaded",
                payload={
                    "document_id": str(document.id),
                    "tenant_id": str(ctx.tenant_id),
                    "blob_path": object_key,
                    "filename": safe_filename,
                    "uploaded_by_user_id": str(ctx.actor_id) if ctx.actor_id else None,
                },
                idempotency_key=f"rag-document-upload-{document.id}",
                aggregate_type="rag_document",
                aggregate_id=str(document.id),
            )
            await write_domain_event_log(
                self._session,
                "rag.document_uploaded",
                aggregate_type="rag_document",
                aggregate_id=str(document.id),
                agency_tenant_id=ctx.tenant_id,
                actor_user_id=ctx.actor_id,
                payload={"document_id": str(document.id), "blob_path": object_key},
            )
            await self._session.commit()
        except Exception:
            try:
                await self._session.rollback()
            except Exception:
                pass
            try:
                delete_object(bucket, object_key)
            except Exception:
                pass
            raise

        return _document_response(document)

    async def get_document(self, document_id: UUID) -> RagDocumentRead:
        ctx = require_tenant(self._tenant)
        document = await self._repo.get_document(document_id, ctx.tenant_id)
        if document is None:
            raise NotFoundError(detail="RAG document not found")
        return _document_response(document)

    async def list_documents(self, page: int, page_size: int) -> PaginatedRagDocumentsResponse:
        ctx = require_tenant(self._tenant)
        pagination = PaginationRequest(page=page, page_size=page_size)
        items, total = await self._repo.list_documents(ctx.tenant_id, pagination)
        return PaginatedRagDocumentsResponse(
            items=[_document_response(item) for item in items],
            total=total,
            page=pagination.page,
            size=pagination.page_size,
        )


def _validate_pdf_upload(file_bytes: bytes, content_type: str | None, filename: str) -> None:
    max_bytes = settings.rag_max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise AppException(
            status_code=400,
            detail=f"Uploaded PDF exceeds maximum size of {settings.rag_max_file_size_mb}MB",
        )
    if not filename.lower().endswith(".pdf"):
        raise AppException(status_code=400, detail="Only PDF files are accepted")
    if not file_bytes.startswith(b"%PDF"):
        raise AppException(status_code=400, detail="Uploaded file is not a valid PDF")
    if content_type and content_type.lower().split(";", 1)[0].strip() not in ("application/pdf", "application/x-pdf"):
        raise AppException(status_code=400, detail="Only PDF files are accepted")
    if not file_bytes.strip():
        raise AppException(status_code=400, detail="Uploaded PDF is empty")


def _sanitize_filename(filename: str) -> str:
    return filename.replace("/", "_").replace("\\", "_") or "document.pdf"


def _build_rag_object_key(tenant_id: UUID, document_id: UUID, filename: str) -> str:
    return f"rag-vault/{tenant_id}/{document_id}/original/{filename}"


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise AppException(status_code=400, detail="PDF text extraction is unavailable") from exc

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise AppException(
            status_code=400,
            detail="Uploaded PDF is empty or unreadable",
        ) from exc
    try:
        text = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
    if not text.strip():
        raise AppException(status_code=400, detail="Uploaded PDF does not contain extractable text")
    return text


def _document_response(document: RagDocument) -> RagDocumentRead:
    response = RagDocumentRead.model_validate(document)
    download_path = f"/api/v1/agencies/rag/documents/{document.id}/download"
    response.document_url = download_path
    response.download_url = download_path
    return response


def hash_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    return " ".join(text.split())
