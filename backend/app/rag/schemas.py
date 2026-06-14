from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    text: Optional[str] = None
    embedding: Optional[list[float]] = None
    status: str = "active"


class RagConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Conversation message content cannot be empty")
        return stripped


class RagRetrievalQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(8, ge=1, le=20)
    include_debug: bool = False
    conversation_messages: list[RagConversationMessage] = Field(default_factory=list)


class RagRetrievalCitation(BaseModel):
    document_id: UUID
    document_filename: str
    page_number: int
    source_label: str


class RagRetrievalEvidence(BaseModel):
    chunk_id: UUID
    document_id: UUID
    page_ids: list[UUID]
    document_filename: str
    page_numbers: list[int]
    source_label: str
    vector_rank: int
    vector_score: float
    rerank_rank: Optional[int] = None
    rerank_score: Optional[float] = None
    text_preview: str
    parent_page_text: Optional[str] = None


class RagRetrievalDebug(BaseModel):
    reranker_used: bool
    reranker_provider: Optional[str] = None
    fallback_reason: Optional[str] = None
    confidence_status: str
    retrieval_log_id: UUID
    guardrail_status: Optional[str] = None
    guardrail_blocked_reason: Optional[str] = None
    generation_provider: Optional[str] = None
    vector_candidate_count: Optional[int] = None
    rerank_candidate_count: Optional[int] = None


class RagPolicyAnswer(BaseModel):
    status: str
    answer: str
    citations: list[RagRetrievalCitation]
    evidence: list[RagRetrievalEvidence]
    debug: Optional[RagRetrievalDebug] = None


class RagRetrievalLogRead(BaseModel):
    id: UUID
    tenant_id: UUID
    document_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    actor_role: str
    query: str
    retrieval_scope: str
    selected_document_ids: list[UUID]
    selected_chunk_ids: list[UUID]
    selected_page_ids: list[UUID]
    reranker_used: bool
    reranker_provider: Optional[str] = None
    fallback_reason: Optional[str] = None
    confidence_status: str
    retrieved_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagRetrievalLogFilter(BaseModel):
    actor_role: Optional[str] = None
    confidence_status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PaginatedRagRetrievalLogsResponse(BaseModel):
    items: list[RagRetrievalLogRead]
    total: int
    page: int
    size: int


class RagEvaluationExampleRead(BaseModel):
    id: str
    query: str
    tenant_fixture: str
    expected_behavior: str
    expected_source_labels: list[str]
    notes: Optional[str] = None
    passed: bool
    summary: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagEvaluationRunRead(BaseModel):
    id: UUID
    run_label: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_examples: int
    passed_examples: int
    failed_examples: int
    summary: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagEvaluationExampleCreate(BaseModel):
    id: str
    query: str
    tenant_fixture: str
    expected_behavior: str
    expected_source_labels: list[str]
    notes: Optional[str] = None
    passed: bool
    summary: dict[str, Any]


class PaginatedRagEvaluationRunsResponse(BaseModel):
    items: list[RagEvaluationRunRead]
    total: int
    page: int
    size: int


class RagChatThreadCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=160)


class RagChatThreadRead(BaseModel):
    id: UUID
    tenant_id: UUID
    owner_user_id: UUID
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagChatMessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(8, ge=1, le=20)
    include_debug: bool = True

    @field_validator("content")
    @classmethod
    def validate_message_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty")
        return stripped


class RagChatMessageRead(BaseModel):
    id: UUID
    thread_id: UUID
    tenant_id: UUID
    owner_user_id: UUID
    role: Literal["user", "assistant"]
    content: str
    sequence_number: int
    retrieval_log_id: Optional[UUID] = None
    answer: Optional[RagPolicyAnswer] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagChatThreadDetailResponse(BaseModel):
    thread: RagChatThreadRead
    messages: list[RagChatMessageRead]


class RagChatSendMessageResponse(BaseModel):
    thread: RagChatThreadRead
    user_message: RagChatMessageRead
    assistant_message: RagChatMessageRead


class PaginatedRagChatThreadsResponse(BaseModel):
    items: list[RagChatThreadRead]
    total: int
    page: int
    size: int
