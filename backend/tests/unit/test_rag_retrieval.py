from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

import pytest

from app.common.tenant import TenantContext
from app.rag.retrieval import RetrievalCandidate, assemble_result, to_policy_answer
from app.rag.schemas import RagRetrievalQueryRequest
from app.rag.service import RagRetrievalService


@pytest.fixture
def tenant_context():
    return TenantContext(
        actor_id=uuid4(),
        role="agency_admin",
        tenant_id=uuid4(),
    )


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.list_processed_documents = AsyncMock(return_value=[MagicMock(id=uuid4())])
    repo.search_chunks_by_embedding = AsyncMock(return_value=[])
    repo.list_parent_pages = AsyncMock(return_value=[])
    repo.create_retrieval_log = AsyncMock(
        return_value=MagicMock(id=uuid4(), created_at=None)
    )
    repo.list_retrieval_logs = AsyncMock(return_value=([], 0))
    repo.get_documents_by_ids = AsyncMock(return_value=[])
    repo.get_chunks_by_ids = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(tenant_context, mock_repo):
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.rollback = AsyncMock()
    svc = RagRetrievalService(mock_session, tenant_context)
    svc._repo = mock_repo
    return svc


class TestRagRetrievalService:
    async def test_answer_policy_query_no_processed_docs(self, service, mock_repo):
        mock_repo.list_processed_documents.return_value = []
        request = RagRetrievalQueryRequest(query="test question")
        result = await service.answer_policy_query(request)

        assert result.status == "insufficient_evidence"
        assert "could not find enough policy evidence" in result.answer.lower()
        assert len(result.citations) == 0
        assert len(result.evidence) == 0
        assert result.debug is not None
        assert result.debug.confidence_status == "insufficient"
        assert result.debug.fallback_reason == "no_processed_documents"

    async def test_answer_policy_query_empty_query_raises(self, service):
        request = RagRetrievalQueryRequest(query="   ")
        with pytest.raises(Exception) as exc:
            await service.answer_policy_query(request)
        assert exc.value.status_code == 400

    def test_answer_policy_query_rejects_invalid_history_role(self):
        with pytest.raises(Exception):
            RagRetrievalQueryRequest(
                query="test question",
                conversation_messages=[{"role": "system", "content": "nope"}],
            )

    async def test_answer_policy_query_insufficient_evidence(self, service, mock_repo):
        mock_repo.search_chunks_by_embedding.return_value = []

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            request = RagRetrievalQueryRequest(query="test question")
            result = await service.answer_policy_query(request)

        assert result.status == "insufficient_evidence"
        assert result.debug.confidence_status == "insufficient"

    async def test_answer_policy_query_reranker_fallback(self, service, mock_repo):
        chunk_id = uuid4()
        doc_id = uuid4()
        mock_doc = MagicMock(id=doc_id, filename="policy.pdf", status="processed")
        mock_chunk = MagicMock(
            id=chunk_id,
            document_id=doc_id,
            page_ids=[uuid4()],
            text="This is a test policy chunk about parking rules.",
            embedding=[0.1] * 1536,
            status="active",
        )
        mock_repo.search_chunks_by_embedding.return_value = [
            (mock_chunk, mock_doc, 0.15)
        ]
        mock_repo.list_parent_pages.return_value = [
            MagicMock(id=mock_chunk.page_ids[0], page_number=1, content="Page context")
        ]
        mock_repo.get_documents_by_ids.return_value = [mock_doc]
        mock_repo.get_chunks_by_ids.return_value = [mock_chunk]

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            with patch("app.rag.service.get_reranking_provider") as mock_rerank:
                mock_rerank.return_value.rerank = AsyncMock(
                    side_effect=RuntimeError("reranker unavailable")
                )
                with patch.object(service, "_generate_grounded_answer", new_callable=AsyncMock) as mock_generate:
                    mock_generate.return_value = {
                        "answer_text": "Visitor parking is limited to 2 hours.",
                        "guardrail_status": "passed",
                        "guardrail_blocked_reason": None,
                        "generation_provider": "nemo_guardrails",
                    }
                    request = RagRetrievalQueryRequest(query="test parking policy")
                    result = await service.answer_policy_query(request)

        assert result.status == "fallback"
        assert "2 hours" in result.answer
        assert len(result.evidence) == 1
        assert len(result.citations) == 1
        assert result.debug.confidence_status == "fallback"
        assert result.debug.reranker_used is True
        assert result.debug.reranker_provider == "openrouter"
        assert result.debug.fallback_reason == "reranker_unavailable"
        assert result.debug.vector_candidate_count == 1
        assert result.debug.rerank_candidate_count == 0

    async def test_answer_policy_query_sufficient(self, service, mock_repo):
        chunk_id = uuid4()
        doc_id = uuid4()
        mock_doc = MagicMock(id=doc_id, filename="policy.pdf", status="processed")
        mock_chunk = MagicMock(
            id=chunk_id,
            document_id=doc_id,
            page_ids=[uuid4()],
            text="Official policy: visitor parking is limited to 2 hours.",
            embedding=[0.1] * 1536,
            status="active",
        )
        mock_repo.search_chunks_by_embedding.return_value = [
            (mock_chunk, mock_doc, 0.08)
        ]
        mock_repo.list_parent_pages.return_value = [
            MagicMock(id=mock_chunk.page_ids[0], page_number=1, content="Page 1 context")
        ]
        mock_repo.get_documents_by_ids.return_value = [mock_doc]
        mock_repo.get_chunks_by_ids.return_value = [mock_chunk]

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            with patch("app.rag.service.get_reranking_provider") as mock_rerank:
                mock_rerank.return_value.rerank = AsyncMock(
                    return_value=[{"index": 0, "document": "chunk text", "score": 0.95}]
                )
                with patch.object(service, "_generate_grounded_answer", new_callable=AsyncMock) as mock_generate:
                    mock_generate.return_value = {
                        "answer_text": "Visitor parking is limited to 2 hours.",
                        "guardrail_status": "passed",
                        "guardrail_blocked_reason": None,
                        "generation_provider": "nemo_guardrails",
                    }
                    request = RagRetrievalQueryRequest(query="visitor parking policy")
                    result = await service.answer_policy_query(request)

        call_args = mock_generate.call_args.kwargs
        assert len(call_args["conversation_messages"]) == 0

        assert result.status == "answered"
        assert result.answer == "Visitor parking is limited to 2 hours."
        assert result.debug.confidence_status == "sufficient"
        assert result.debug.reranker_used is True
        assert result.debug.vector_candidate_count == 1
        assert result.debug.rerank_candidate_count == 1
        assert len(result.citations) == 1
        citation = result.citations[0]
        assert citation.document_filename == "policy.pdf"
        assert citation.page_number == 1

    async def test_answer_policy_query_truncates_history(self, service, mock_repo):
        chunk_id = uuid4()
        doc_id = uuid4()
        mock_doc = MagicMock(id=doc_id, filename="policy.pdf", status="processed")
        mock_chunk = MagicMock(
            id=chunk_id,
            document_id=doc_id,
            page_ids=[uuid4()],
            text="Official policy: visitor parking is limited to 2 hours.",
            embedding=[0.1] * 1536,
            status="active",
        )
        mock_repo.search_chunks_by_embedding.return_value = [(mock_chunk, mock_doc, 0.08)]
        mock_repo.list_parent_pages.return_value = [
            MagicMock(id=mock_chunk.page_ids[0], page_number=1, content="Page 1 context")
        ]
        mock_repo.get_documents_by_ids.return_value = [mock_doc]
        mock_repo.get_chunks_by_ids.return_value = [mock_chunk]

        history = [
            {"role": "user", "content": f"User {idx}"} if idx % 2 == 0 else {"role": "assistant", "content": f"Assistant {idx}"}
            for idx in range(12)
        ]

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            with patch("app.rag.service.get_reranking_provider") as mock_rerank:
                mock_rerank.return_value.rerank = AsyncMock(
                    return_value=[{"index": 0, "document": "chunk text", "score": 0.95}]
                )
                with patch.object(service, "_generate_grounded_answer", new_callable=AsyncMock) as mock_generate:
                    mock_generate.return_value = {
                        "answer_text": "Visitor parking is limited to 2 hours.",
                        "guardrail_status": "passed",
                        "guardrail_blocked_reason": None,
                        "generation_provider": "nemo_guardrails",
                    }
                    request = RagRetrievalQueryRequest(
                        query="visitor parking policy",
                        conversation_messages=history,
                    )
                    await service.answer_policy_query(request)

        call_args = mock_generate.call_args.kwargs
        assert len(call_args["conversation_messages"]) == 8

    async def test_retrieval_log_rbac_agency_admin_allowed(self, service):
        service._tenant.role = "agency_admin"
        mock_repo = service._repo
        mock_repo.list_retrieval_logs.return_value = ([], 0)
        result = await service.list_retrieval_logs(page=1, page_size=20)
        assert result.total == 0

    async def test_retrieval_log_rbac_support_employee_denied(self, service):
        service._tenant.role = "support_employee"
        with pytest.raises(Exception) as exc:
            await service.list_retrieval_logs(page=1, page_size=20)
        assert "agency admin" in str(exc.value).lower()

    async def test_retrieval_log_with_filters(self, service):
        from app.rag.schemas import RagRetrievalLogFilter

        service._tenant.role = "agency_admin"
        mock_repo = service._repo
        mock_repo.list_retrieval_logs.return_value = ([], 0)

        filters = RagRetrievalLogFilter(confidence_status="sufficient")
        result = await service.list_retrieval_logs(page=1, page_size=20, filters=filters)
        assert result.total == 0

        call_args = mock_repo.list_retrieval_logs.call_args
        assert call_args[0][2] is filters


class TestRerankingLogic:
    def test_assemble_result_answered_status(self):
        candidate = RetrievalCandidate(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_filename="policy.pdf",
            page_ids=[uuid4()],
            page_numbers=[1],
            text="Policy text about parking.",
            vector_rank=1,
            vector_score=0.92,
            rerank_rank=1,
            rerank_score=0.95,
        )
        result = assemble_result(
            "test query",
            [candidate],
            answer_text="Parking is limited to 2 hours.",
            reranker_used=True,
            reranker_provider="openrouter",
            fallback_reason=None,
            confidence_status="sufficient",
            retrieval_log_id=uuid4(),
        )
        assert result.status == "answered"
        assert result.answer == "Parking is limited to 2 hours."
        assert len(result.citations) == 1
        assert len(result.evidence) == 1
        assert result.debug.reranker_used is True
        assert result.debug.confidence_status == "sufficient"

    def test_assemble_result_insufficient_evidence(self):
        result = assemble_result(
            "test query",
            [],
            answer_text=None,
            reranker_used=False,
            reranker_provider=None,
            fallback_reason="no_processed_documents",
            confidence_status="insufficient",
            retrieval_log_id=uuid4(),
        )
        assert result.status == "insufficient_evidence"
        assert len(result.citations) == 0
        assert len(result.evidence) == 0
        assert result.debug.fallback_reason == "no_processed_documents"

    def test_assemble_result_fallback(self):
        candidate = RetrievalCandidate(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_filename="policy.pdf",
            page_ids=[uuid4()],
            page_numbers=[1],
            text="Some policy text.",
            vector_rank=1,
            vector_score=0.5,
        )
        result = assemble_result(
            "test query",
            [candidate],
            answer_text="I found partial evidence about the policy.",
            reranker_used=True,
            reranker_provider="openrouter",
            fallback_reason="reranker_unavailable",
            confidence_status="fallback",
            retrieval_log_id=uuid4(),
        )
        assert result.status == "fallback"
        assert "partial evidence" in result.answer
        assert result.debug.confidence_status == "fallback"
        assert result.debug.fallback_reason == "reranker_unavailable"

    def test_assemble_result_parent_page_text(self):
        page_id = uuid4()
        candidate = RetrievalCandidate(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_filename="policy.pdf",
            page_ids=[page_id],
            page_numbers=[1],
            text="Chunk text.",
            vector_rank=1,
            vector_score=0.9,
        )
        result = assemble_result(
            "test query",
            [candidate],
            answer_text="Policy text found on page 1.",
            reranker_used=False,
            reranker_provider=None,
            fallback_reason=None,
            confidence_status="sufficient",
            retrieval_log_id=uuid4(),
            parent_page_text={page_id: "Full page context for the chunk."},
        )
        assert result.evidence[0].parent_page_text is not None


class TestToPolicyAnswer:
    def test_to_policy_answer_maps_fields(self):
        candidate = RetrievalCandidate(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_filename="policy.pdf",
            page_ids=[uuid4()],
            page_numbers=[1],
            text="Policy text.",
            vector_rank=1,
            vector_score=0.9,
        )
        assembled = assemble_result(
            "query",
            [candidate],
            answer_text="Grounded answer.",
            reranker_used=False,
            reranker_provider=None,
            fallback_reason=None,
            confidence_status="sufficient",
            retrieval_log_id=uuid4(),
        )
        answer = to_policy_answer(assembled)

        assert answer.status == assembled.status
        assert answer.answer == assembled.answer
        assert len(answer.citations) == len(assembled.citations)
        assert len(answer.evidence) == len(assembled.evidence)
        assert answer.debug is not None
        assert answer.debug.confidence_status == "sufficient"
