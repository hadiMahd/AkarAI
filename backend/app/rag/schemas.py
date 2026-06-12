from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RagDocumentCreate(BaseModel):
    tenant_id: UUID
    filename: str = Field(..., min_length=1, max_length=512)
    blob_path: str = Field(..., min_length=1, max_length=1024)
    status: str = "pending"


class RagDocumentRead(BaseModel):
    id: UUID
    tenant_id: UUID
    filename: str
    status: str
    blob_path: str
    document_url: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedRagDocumentsResponse(BaseModel):
    items: list[RagDocumentRead]
    total: int
    page: int
    size: int


class RagPageCreate(BaseModel):
    document_id: UUID
    tenant_id: UUID
    page_number: int = Field(..., ge=1)
    blob_path: str = Field(..., min_length=1, max_length=1024)


class RagChunkCreate(BaseModel):
    document_id: UUID
    tenant_id: UUID
    page_ids: list[UUID]
    content_hash: str = Field(..., min_length=64, max_length=64)
    embedding: Optional[list[float]] = None
    status: str = "active"
