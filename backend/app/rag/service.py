import json
from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID, uuid4

from app.ai.guardrails import generate_guardrailed_policy_answer
from app.ai.registry import get_embedding_provider, get_reranking_provider
from app.common.exceptions import AppException, ForbiddenError, NotFoundError
from app.common.pagination import PaginationRequest
from app.common.config import settings
from app.common.redis import redis_get, redis_set
from app.common.storage import delete_object, ensure_bucket_exists, get_rag_bucket, upload_object
from app.common.tenant import TenantContext, require_tenant
from app.rag.models import (
    RagChatMessage,
    RagChatThread,
    RagDocument,
    RagEvaluationExample,
    RagEvaluationRun,
    RagRetrievalLog,
)
from app.rag.repository import RagRepository
from app.rag.redaction import redact_text, sanitize_answer_payload
from app.rag.retrieval import RetrievalCandidate, assemble_result, to_policy_answer, truncate_text
from app.rag.schemas import (
    PaginatedRagChatThreadsResponse,
    PaginatedRagDocumentsResponse,
    PaginatedRagRetrievalLogsResponse,
    RagChatMessageCreateRequest,
    RagChatMessageRead,
    RagChatSendMessageResponse,
    RagChatThreadCreateRequest,
    RagChatThreadDetailResponse,
    RagChatThreadRead,
    RagDocumentRead,
    RagEvaluationExampleCreate,
    RagEvaluationRunRead,
    RagPolicyAnswer,
    RagRetrievalLogFilter,
    RagRetrievalQueryRequest,
    RagRetrievalLogRead,
)
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

    async def replace_document(
        self,
        document_id: UUID,
        file_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> RagDocumentRead:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot replace RAG documents")

        document = await self._repo.get_document(document_id, ctx.tenant_id)
        if document is None:
            raise NotFoundError(detail="RAG document not found")
        if document.status == "processing":
            raise AppException(status_code=409, detail="Document is already processing")

        safe_filename = _sanitize_filename(filename)
        _validate_pdf_upload(file_bytes, content_type, safe_filename)
        try:
            _extract_text_from_pdf(file_bytes)
        except AppException:
            raise
        except Exception as exc:
            raise AppException(
                status_code=400,
                detail="Uploaded PDF does not contain extractable text",
            ) from exc

        bucket = get_rag_bucket()
        ensure_bucket_exists(bucket)
        previous_blob_path = document.blob_path
        next_blob_path = _build_rag_object_key(ctx.tenant_id, document.id, safe_filename)

        try:
            upload_object(bucket, next_blob_path, file_bytes, "application/pdf")
        except Exception as exc:
            raise AppException(status_code=503, detail=f"Failed to store document: {exc}") from exc

        replaced_blob_uploaded = True
        document.filename = safe_filename
        document.blob_path = next_blob_path
        document.status = "pending"

        try:
            document = await self._repo.update_document(document)

            await publish_outbox_event_in_session(
                self._session,
                event_name="rag.document_uploaded",
                payload={
                    "document_id": str(document.id),
                    "tenant_id": str(ctx.tenant_id),
                    "blob_path": next_blob_path,
                    "filename": safe_filename,
                    "uploaded_by_user_id": str(ctx.actor_id) if ctx.actor_id else None,
                },
                idempotency_key=f"rag-document-replace-{document.id}-{uuid4()}",
                aggregate_type="rag_document",
                aggregate_id=str(document.id),
            )
            await write_domain_event_log(
                self._session,
                "rag.document_replaced",
                aggregate_type="rag_document",
                aggregate_id=str(document.id),
                agency_tenant_id=ctx.tenant_id,
                actor_user_id=ctx.actor_id,
                payload={
                    "document_id": str(document.id),
                    "previous_blob_path": previous_blob_path,
                    "blob_path": next_blob_path,
                },
            )
            await self._session.commit()
        except Exception:
            try:
                await self._session.rollback()
            except Exception:
                pass
            if replaced_blob_uploaded:
                try:
                    delete_object(bucket, next_blob_path)
                except Exception:
                    pass
            raise

        if previous_blob_path != next_blob_path:
            try:
                delete_object(bucket, previous_blob_path)
            except Exception:
                pass

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


class RagRetrievalService:
    def __init__(self, session, tenant: TenantContext | None = None):
        self._session = session
        self._tenant = tenant
        self._repo = RagRepository(session)

    async def list_retrieval_logs(
        self,
        page: int,
        page_size: int,
        filters: RagRetrievalLogFilter | None = None,
    ) -> PaginatedRagRetrievalLogsResponse:
        ctx = require_tenant(self._tenant)
        if ctx.role not in ("agency_admin", "platform_admin"):
            raise ForbiddenError(
                detail="Only agency admins can view retrieval logs",
                error_code="ROLE_DENIED",
            )
        pagination = PaginationRequest(page=page, page_size=page_size)
        items, total = await self._repo.list_retrieval_logs(ctx.tenant_id, pagination, filters)
        return PaginatedRagRetrievalLogsResponse(
            items=[_retrieval_log_response(item) for item in items],
            total=total,
            page=pagination.page,
            size=pagination.page_size,
        )

    async def create_retrieval_log(
        self,
        *,
        query: str,
        actor_role: str,
        document_ids: list[UUID] | None = None,
        chunk_ids: list[UUID] | None = None,
        page_ids: list[UUID] | None = None,
        reranker_used: bool = False,
        reranker_provider: str | None = None,
        fallback_reason: str | None = None,
        confidence_status: str = "sufficient",
        document_id: UUID | None = None,
        actor_user_id: UUID | None = None,
    ) -> RagRetrievalLogRead:
        ctx = require_tenant(self._tenant)
        log = RagRetrievalLog(
            tenant_id=ctx.tenant_id,
            document_id=document_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            query=query,
            retrieval_scope="agency_policy",
            selected_document_ids=document_ids or [],
            selected_chunk_ids=chunk_ids or [],
            selected_page_ids=page_ids or [],
            reranker_used=reranker_used,
            reranker_provider=reranker_provider,
            fallback_reason=fallback_reason,
            confidence_status=confidence_status,
            retrieved_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        log = await self._repo.create_retrieval_log(log)
        await self._session.commit()
        return _retrieval_log_response(log)

    async def record_evaluation_run(
        self,
        *,
        run_label: str,
        total_examples: int,
        passed_examples: int,
        failed_examples: int,
        summary: dict,
    ) -> RagEvaluationRunRead:
        run = RagEvaluationRun(
            run_label=run_label,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_examples=total_examples,
            passed_examples=passed_examples,
            failed_examples=failed_examples,
            summary=summary,
            created_at=datetime.now(timezone.utc),
        )
        run = await self._repo.create_evaluation_run(run)
        await self._session.commit()
        return _evaluation_run_response(run)

    async def record_evaluation_run_with_examples(
        self,
        *,
        run_label: str,
        examples: list[RagEvaluationExampleCreate],
        summary: dict | None = None,
    ) -> RagEvaluationRunRead:
        total = len(examples)
        passed = sum(1 for e in examples if e.passed)
        failed = total - passed
        actual_summary = summary or {
            "total_examples": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total, 4) if total > 0 else 0.0,
            "latency_ms": {},
        }
        run = RagEvaluationRun(
            run_label=run_label,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_examples=total,
            passed_examples=passed,
            failed_examples=failed,
            summary=actual_summary,
            created_at=datetime.now(timezone.utc),
        )
        run = await self._repo.create_evaluation_run(run)
        example_models = [
            RagEvaluationExample(
                id=ex.id,
                run_id=run.id,
                query=ex.query,
                tenant_fixture=ex.tenant_fixture,
                expected_behavior=ex.expected_behavior,
                expected_source_labels=ex.expected_source_labels,
                notes=ex.notes,
                passed=ex.passed,
                summary=ex.summary,
            )
            for ex in examples
        ]
        await self._repo.create_evaluation_examples(example_models)
        await self._session.commit()
        return _evaluation_run_response(run)

    async def build_policy_answer(
        self,
        query: str,
        candidates: list[RetrievalCandidate],
        *,
        answer_text: str | None = None,
        reranker_used: bool,
        reranker_provider: str | None,
        fallback_reason: str | None,
        confidence_status: str,
        retrieval_log_id: UUID,
        parent_page_text: dict[UUID, str] | None = None,
    ) -> RagPolicyAnswer:
        return to_policy_answer(
            assemble_result(
                query,
                candidates,
                answer_text=answer_text,
                reranker_used=reranker_used,
                reranker_provider=reranker_provider,
                fallback_reason=fallback_reason,
                confidence_status=confidence_status,
                retrieval_log_id=retrieval_log_id,
                parent_page_text=parent_page_text,
                guardrail_status=None,
                guardrail_blocked_reason=None,
                generation_provider=None,
            )
        )

    async def answer_policy_query(
        self,
        request: RagRetrievalQueryRequest,
    ) -> RagPolicyAnswer:
        ctx = require_tenant(self._tenant)
        query = request.query.strip()
        top_k = request.top_k
        include_debug = request.include_debug
        conversation_messages = _trim_conversation_messages(
            [message.model_dump() for message in request.conversation_messages]
        )

        if not query:
            raise AppException(status_code=400, detail="Query cannot be empty")

        # 1. Fetch processed documents for the tenant as a snapshot
        processed_docs = await self._repo.list_processed_documents(ctx.tenant_id)
        if not processed_docs:
            retrieval_log = await self._create_log_for_result(
                query=query,
                actor_role=ctx.role,
                actor_user_id=ctx.actor_id,
                confidence_status="insufficient",
            )
            answer = to_policy_answer(
                assemble_result(
                    query,
                    [],
                    answer_text=None,
                    reranker_used=False,
                    reranker_provider=None,
                    fallback_reason="no_processed_documents",
                    confidence_status="insufficient",
                    retrieval_log_id=retrieval_log.id,
                    guardrail_status=None,
                    guardrail_blocked_reason=None,
                    generation_provider=None,
                )
            )
            answer.debug.vector_candidate_count = 0
            answer.debug.rerank_candidate_count = 0
            await self._session.commit()
            return answer

        # 2. Generate embedding for query
        try:
            embedding_provider = get_embedding_provider()
            query_embeddings = await embedding_provider.embed([query])
        except Exception as exc:
            raise AppException(
                status_code=503,
                detail=f"Failed to generate query embedding: {exc}",
            ) from exc

        query_embedding = query_embeddings[0]

        # 3. Vector search for similar chunks
        try:
            chunk_doc_distances = await self._repo.search_chunks_by_embedding(
                ctx.tenant_id, query_embedding, top_k=top_k,
            )
        except Exception as exc:
            raise AppException(
                status_code=503,
                detail=f"Vector search failed: {exc}",
            ) from exc

        if not chunk_doc_distances:
            retrieval_log = await self._create_log_for_result(
                query=query,
                actor_role=ctx.role,
                actor_user_id=ctx.actor_id,
                confidence_status="insufficient",
            )
            answer = to_policy_answer(
                assemble_result(
                    query,
                    [],
                    answer_text=None,
                    reranker_used=False,
                    reranker_provider=None,
                    fallback_reason="no_vector_results",
                    confidence_status="insufficient",
                    retrieval_log_id=retrieval_log.id,
                    guardrail_status=None,
                    guardrail_blocked_reason=None,
                    generation_provider=None,
                )
            )
            answer.debug.vector_candidate_count = 0
            answer.debug.rerank_candidate_count = 0
            await self._session.commit()
            return answer

        # 4. Build candidates from vector search results
        # Collect all page_ids needed for page_number lookups
        all_page_ids: set[UUID] = set()
        for chunk, doc, distance in chunk_doc_distances:
            all_page_ids.update(chunk.page_ids)

        # Fetch parent pages to get page numbers and text
        parent_pages = await self._repo.list_parent_pages(ctx.tenant_id, list(all_page_ids))
        page_id_to_number: dict[UUID, int] = {p.id: p.page_number for p in parent_pages}
        page_id_to_text: dict[UUID, str] = {
            p.id: p.content or "" for p in parent_pages if p.content
        }

        # Verify documents are still processed (replace-while-retrieving hardening)
        unique_doc_ids = {doc.id for _, doc, _ in chunk_doc_distances}
        refreshed_docs = await self._repo.get_documents_by_ids(
            ctx.tenant_id, list(unique_doc_ids)
        )
        refreshed_doc_map = {d.id: d for d in refreshed_docs}
        stale_doc_ids = [
            did for did in unique_doc_ids
            if did not in refreshed_doc_map or refreshed_doc_map[did].status != "processed"
        ]
        if stale_doc_ids:
            filtered_distances = [
                (c, d, dist) for c, d, dist in chunk_doc_distances
                if d.id not in stale_doc_ids
            ]
            if not filtered_distances:
                retrieval_log = await self._create_log_for_result(
                    query=query,
                    actor_role=ctx.role,
                    actor_user_id=ctx.actor_id,
                    confidence_status="insufficient",
                )
                answer = to_policy_answer(
                    assemble_result(
                        query,
                        [],
                        answer_text=None,
                        reranker_used=False,
                        reranker_provider=None,
                        fallback_reason="documents_replaced_during_retrieval",
                        confidence_status="insufficient",
                        retrieval_log_id=retrieval_log.id,
                        guardrail_status=None,
                        guardrail_blocked_reason=None,
                        generation_provider=None,
                    )
                )
                answer.debug.vector_candidate_count = 0
                answer.debug.rerank_candidate_count = 0
                await self._session.commit()
                return answer
            chunk_doc_distances = filtered_distances

        vector_candidates: list[RetrievalCandidate] = []
        for rank, (chunk, doc, distance) in enumerate(chunk_doc_distances, start=1):
            page_numbers = sorted(
                page_id_to_number.get(pid, 0) for pid in chunk.page_ids
            )
            vector_candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    document_filename=doc.filename,
                    page_ids=list(chunk.page_ids),
                    page_numbers=page_numbers,
                    text=chunk.text or "",
                    vector_rank=rank,
                    vector_score=1.0 - min(distance, 1.0),
                )
            )

        # 5. Rerank via OpenRouter with graceful fallback
        reranker_used = False
        reranker_provider = None
        fallback_reason: str | None = None
        rerank_candidate_count: int | None = None

        try:
            reranker = get_reranking_provider()
            reranker_used = True
            reranker_provider = "openrouter"
            chunk_texts = [c.text for c in vector_candidates]
            if chunk_texts:
                rerank_results = await reranker.rerank(query, chunk_texts)
                if rerank_results and len(rerank_results) > 0:
                    rerank_candidate_count = len(rerank_results)
                    # Build rank map from reranker results
                    rerank_map: dict[int, int] = {}
                    rerank_score_map: dict[int, float] = {}
                    for rr_idx, rr in enumerate(rerank_results, start=1):
                        orig_index = rr.get("index", rr_idx - 1)
                        rerank_map[orig_index] = rr_idx
                        rerank_score_map[orig_index] = rr.get("score", 0.0)

                    # Apply reranking to candidates
                    reranked_candidates: list[RetrievalCandidate] = []
                    for orig_idx, candidate in enumerate(vector_candidates):
                        candidate.rerank_rank = rerank_map.get(orig_idx, orig_idx + 1)
                        candidate.rerank_score = rerank_score_map.get(orig_idx, 0.0)
                        reranked_candidates.append(candidate)

                    # Sort by rerank rank
                    reranked_candidates.sort(key=lambda c: c.rerank_rank or 999)
                    vector_candidates = reranked_candidates
        except Exception:
            fallback_reason = "reranker_unavailable"

        # 6. Fetch parent page text for evidence
        parent_page_text: dict[UUID, str] = {}
        for candidate in vector_candidates:
            for pid in candidate.page_ids:
                if pid not in parent_page_text and pid in page_id_to_text:
                    parent_page_text[pid] = page_id_to_text[pid]

        # 7. Determine confidence
        if not vector_candidates:
            confidence_status = "insufficient"
        elif fallback_reason:
            confidence_status = "fallback"
        else:
            confidence_status = "sufficient"

        answer_text: str | None = None
        guardrail_status: str | None = None
        guardrail_blocked_reason: str | None = None
        generation_provider: str | None = None
        if vector_candidates:
            try:
                generation_result = await self._generate_grounded_answer(
                    query=query,
                    candidates=vector_candidates,
                    parent_page_text=parent_page_text,
                    confidence_status=confidence_status,
                    conversation_messages=conversation_messages,
                )
                answer_text = redact_text(generation_result["answer_text"] or "")
                guardrail_status = generation_result["guardrail_status"]
                guardrail_blocked_reason = generation_result["guardrail_blocked_reason"]
                generation_provider = generation_result["generation_provider"]
                if guardrail_status == "blocked":
                    fallback_reason = guardrail_blocked_reason or "guardrail_blocked"
                    confidence_status = "fallback"
            except Exception:
                if not fallback_reason:
                    fallback_reason = "answer_generation_unavailable"
                confidence_status = "fallback"

        # 8. Create retrieval log
        selected_doc_ids = list({c.document_id for c in vector_candidates})
        selected_chunk_ids = [c.chunk_id for c in vector_candidates]
        selected_page_ids = list({
            pid for c in vector_candidates for pid in c.page_ids
        })

        log = RagRetrievalLog(
            tenant_id=ctx.tenant_id,
            actor_user_id=ctx.actor_id,
            actor_role=ctx.role,
            query=query,
            retrieval_scope="agency_policy",
            selected_document_ids=selected_doc_ids,
            selected_chunk_ids=selected_chunk_ids,
            selected_page_ids=selected_page_ids,
            reranker_used=reranker_used,
            reranker_provider=reranker_provider,
            fallback_reason=fallback_reason,
            confidence_status=confidence_status,
            retrieved_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        log = await self._repo.create_retrieval_log(log)

        # 9. Assemble final answer
        answer = to_policy_answer(
            assemble_result(
                query,
                vector_candidates,
                answer_text=answer_text,
                reranker_used=reranker_used,
                reranker_provider=reranker_provider,
                fallback_reason=fallback_reason,
                confidence_status=confidence_status,
                retrieval_log_id=log.id,
                parent_page_text=parent_page_text,
                guardrail_status=guardrail_status,
                guardrail_blocked_reason=guardrail_blocked_reason,
                generation_provider=generation_provider,
            )
        )
        if include_debug and answer.debug:
            answer.debug.vector_candidate_count = len(chunk_doc_distances)
            answer.debug.rerank_candidate_count = rerank_candidate_count

        await self._session.commit()
        return _sanitize_policy_answer(answer)

    async def _generate_grounded_answer(
        self,
        *,
        query: str,
        candidates: list[RetrievalCandidate],
        parent_page_text: dict[UUID, str],
        confidence_status: str,
        conversation_messages: list[dict[str, str]],
    ) -> dict[str, str | None]:
        context_blocks = _build_evidence_blocks(candidates, parent_page_text)
        generation = await generate_guardrailed_policy_answer(
            query=query,
            evidence_blocks=context_blocks,
            conversation_messages=conversation_messages,
            tenant_context=require_tenant(self._tenant),
            confidence_status=confidence_status,
        )
        return {
            "answer_text": generation.answer_text,
            "guardrail_status": generation.guardrail_status,
            "guardrail_blocked_reason": generation.blocked_reason,
            "generation_provider": generation.generation_provider,
        }

    async def _create_log_for_result(
        self,
        *,
        query: str,
        actor_role: str,
        actor_user_id: UUID | None,
        confidence_status: str = "insufficient",
    ) -> RagRetrievalLog:
        ctx = require_tenant(self._tenant)
        log = RagRetrievalLog(
            tenant_id=ctx.tenant_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            query=query,
            retrieval_scope="agency_policy",
            selected_document_ids=[],
            selected_chunk_ids=[],
            selected_page_ids=[],
            reranker_used=False,
            reranker_provider=None,
            fallback_reason=None,
            confidence_status=confidence_status,
            retrieved_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        log = await self._repo.create_retrieval_log(log)
        return log


class RagChatService:
    def __init__(self, session, tenant: TenantContext | None = None):
        self._session = session
        self._tenant = tenant
        self._repo = RagRepository(session)

    async def create_thread(
        self,
        request: RagChatThreadCreateRequest | None = None,
    ) -> RagChatThreadRead:
        ctx = require_tenant(self._tenant)
        if ctx.actor_id is None:
            raise ForbiddenError(detail="Authenticated user required")
        title = (request.title.strip() if request and request.title else "") or "New conversation"
        title = title[:160]
        now = datetime.now(timezone.utc)
        thread = RagChatThread(
            tenant_id=ctx.tenant_id,
            owner_user_id=ctx.actor_id,
            title=title,
            created_at=now,
            updated_at=now,
            last_message_at=now,
        )
        thread = await self._repo.create_chat_thread(thread)
        await self._session.commit()
        return _chat_thread_response(thread, 0)

    async def list_threads(self, page: int, page_size: int) -> PaginatedRagChatThreadsResponse:
        ctx = require_tenant(self._tenant)
        if ctx.actor_id is None:
            raise ForbiddenError(detail="Authenticated user required")
        pagination = PaginationRequest(page=page, page_size=page_size)
        rows, total = await self._repo.list_chat_threads(ctx.tenant_id, ctx.actor_id, pagination)
        return PaginatedRagChatThreadsResponse(
            items=[_chat_thread_response(thread, message_count) for thread, message_count in rows],
            total=total,
            page=pagination.page,
            size=pagination.page_size,
        )

    async def get_thread(self, thread_id: UUID) -> RagChatThreadDetailResponse:
        ctx = require_tenant(self._tenant)
        if ctx.actor_id is None:
            raise ForbiddenError(detail="Authenticated user required")
        cache_key = _rag_chat_cache_key(ctx.tenant_id, ctx.actor_id, thread_id)
        cached = await redis_get(cache_key)
        if cached:
            return RagChatThreadDetailResponse.model_validate_json(cached)

        thread = await self._repo.get_chat_thread(thread_id, ctx.tenant_id, ctx.actor_id)
        if thread is None:
            raise NotFoundError(detail="Chat thread not found")
        messages = await self._repo.list_chat_messages(thread_id, ctx.tenant_id, ctx.actor_id)
        detail = RagChatThreadDetailResponse(
            thread=_chat_thread_response(thread, len(messages)),
            messages=[_chat_message_response(message) for message in messages],
        )
        sanitized_detail = sanitize_answer_payload(detail.model_dump(mode="json"))
        await redis_set(cache_key, json.dumps(sanitized_detail), ttl=settings.rag_chat_redis_ttl_seconds)
        return detail

    async def send_message(
        self,
        thread_id: UUID,
        request: RagChatMessageCreateRequest,
    ) -> RagChatSendMessageResponse:
        ctx = require_tenant(self._tenant)
        if ctx.actor_id is None:
            raise ForbiddenError(detail="Authenticated user required")
        thread = await self._repo.get_chat_thread(thread_id, ctx.tenant_id, ctx.actor_id)
        if thread is None:
            raise NotFoundError(detail="Chat thread not found")

        existing_messages = await self._repo.list_chat_messages(thread_id, ctx.tenant_id, ctx.actor_id)
        next_sequence = await self._repo.get_next_chat_sequence_number(thread_id)
        user_message = RagChatMessage(
            thread_id=thread.id,
            tenant_id=ctx.tenant_id,
            owner_user_id=ctx.actor_id,
            role="user",
            content=request.content.strip(),
            sequence_number=next_sequence,
            created_at=datetime.now(timezone.utc),
        )
        user_message = await self._repo.create_chat_message(user_message)
        if thread.title == "New conversation":
            thread.title = _derive_thread_title(user_message.content)
        now = datetime.now(timezone.utc)
        thread.updated_at = now
        thread.last_message_at = now
        await self._repo.update_chat_thread(thread)
        await self._session.commit()

        retrieval_service = RagRetrievalService(self._session, self._tenant)
        answer = await retrieval_service.answer_policy_query(
            RagRetrievalQueryRequest(
                query=user_message.content,
                top_k=request.top_k,
                include_debug=request.include_debug,
                conversation_messages=_conversation_messages_from_chat(existing_messages),
            )
        )
        retrieval_log_id = answer.debug.retrieval_log_id if answer.debug else None

        assistant_sequence = await self._repo.get_next_chat_sequence_number(thread_id)
        sanitized_answer_payload = sanitize_answer_payload(answer.model_dump(mode="json"))
        assistant_message = RagChatMessage(
            thread_id=thread.id,
            tenant_id=ctx.tenant_id,
            owner_user_id=ctx.actor_id,
            role="assistant",
            content=redact_text(answer.answer),
            sequence_number=assistant_sequence,
            retrieval_log_id=retrieval_log_id,
            answer_payload=sanitized_answer_payload,
            created_at=datetime.now(timezone.utc),
        )
        assistant_message = await self._repo.create_chat_message(assistant_message)
        thread.updated_at = assistant_message.created_at
        thread.last_message_at = assistant_message.created_at
        await self._repo.update_chat_thread(thread)
        await self._session.commit()

        refreshed_messages = existing_messages + [user_message, assistant_message]
        detail = RagChatThreadDetailResponse(
            thread=_chat_thread_response(thread, len(refreshed_messages)),
            messages=[_chat_message_response(message) for message in refreshed_messages],
        )
        sanitized_cache = sanitize_answer_payload(detail.model_dump(mode="json"))
        await redis_set(
            _rag_chat_cache_key(ctx.tenant_id, ctx.actor_id, thread.id),
            json.dumps(sanitized_cache),
            ttl=settings.rag_chat_redis_ttl_seconds,
        )
        return RagChatSendMessageResponse(
            thread=detail.thread,
            user_message=_chat_message_response(user_message),
            assistant_message=_chat_message_response(assistant_message),
        )


def _retrieval_log_response(log: RagRetrievalLog) -> RagRetrievalLogRead:
    return RagRetrievalLogRead.model_validate(log)


def _evaluation_run_response(run: RagEvaluationRun) -> RagEvaluationRunRead:
    return RagEvaluationRunRead.model_validate(run)


def _chat_thread_response(thread: RagChatThread, message_count: int) -> RagChatThreadRead:
    return RagChatThreadRead(
        id=thread.id,
        tenant_id=thread.tenant_id,
        owner_user_id=thread.owner_user_id,
        title=thread.title,
        message_count=message_count,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        last_message_at=thread.last_message_at,
    )


def _chat_message_response(message: RagChatMessage) -> RagChatMessageRead:
    answer = None
    if message.answer_payload:
        answer = RagPolicyAnswer.model_validate(message.answer_payload)
    return RagChatMessageRead(
        id=message.id or uuid4(),
        thread_id=message.thread_id,
        tenant_id=message.tenant_id,
        owner_user_id=message.owner_user_id,
        role=message.role,
        content=message.content,
        sequence_number=message.sequence_number,
        retrieval_log_id=message.retrieval_log_id,
        answer=answer,
        created_at=message.created_at,
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


def _trim_conversation_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    max_messages = max(0, settings.ai_guardrails_max_history_turns * 2)
    trimmed = messages[-max_messages:]
    normalized: list[dict[str, str]] = []
    for message in trimmed:
        role = message.get("role", "").strip()
        content = message.get("content", "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append(
            {
                "role": role,
                "content": content[: settings.ai_guardrails_max_message_chars],
            }
        )
    return normalized


def _conversation_messages_from_chat(messages: list[RagChatMessage]) -> list[dict[str, str]]:
    raw = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
        if message.role in {"user", "assistant"} and message.content
    ]
    return _trim_conversation_messages(raw)


def _derive_thread_title(content: str) -> str:
    compact = " ".join(content.split())
    return (compact[:77] + "...") if len(compact) > 80 else compact


def _rag_chat_cache_key(tenant_id: UUID, owner_user_id: UUID, thread_id: UUID) -> str:
    return f"rag_policy_chat:{tenant_id}:{owner_user_id}:{thread_id}"


def _build_evidence_blocks(
    candidates: list[RetrievalCandidate],
    parent_page_text: dict[UUID, str],
) -> list[str]:
    context_blocks: list[str] = []
    for index, candidate in enumerate(candidates[:6], start=1):
        page_context = " ".join(
            parent_page_text.get(page_id, "")
            for page_id in candidate.page_ids
            if parent_page_text.get(page_id)
        ).strip()
        evidence_text = page_context or candidate.text
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {index}] {candidate.document_filename} | pages {', '.join(str(page) for page in candidate.page_numbers if page)}",
                    truncate_text(evidence_text or candidate.text, 1600),
                ]
            )
        )
    return context_blocks


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


def _sanitize_policy_answer(answer: RagPolicyAnswer) -> RagPolicyAnswer:
    """Return a new RagPolicyAnswer with all string content sanitized.

    Rebuilds the object from its sanitized dict representation so the caller
    always receives a clean payload with no secret-like strings in the answer
    text, evidence previews, or debug fields.
    """
    sanitized = sanitize_answer_payload(answer.model_dump(mode="json"))
    return RagPolicyAnswer.model_validate(sanitized)


def hash_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    return " ".join(text.split())
