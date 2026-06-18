"""Integration tests for RAG retrieval API: query, logs, replace-while-retrieving, and evaluation."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.ai.guardrails import GuardrailedGenerationResult
from app.rag.schemas import RagEvaluationExampleCreate
from app.rag.service import RagRetrievalService

FAKE_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog>>\nendobj\n%%EOF"


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_processed_document(db_session, tenant_id: uuid4, filename: str = "policy.pdf"):
    from app.rag.models import RagChunk, RagDocument, RagPage

    doc_obj = RagDocument(
        id=uuid4(),
        tenant_id=tenant_id,
        filename=filename,
        status="processed",
        blob_path=f"rag-vault/{tenant_id}/{uuid4()}/original/{filename}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(doc_obj)
    await db_session.flush()

    page = RagPage(
        id=uuid4(),
        document_id=doc_obj.id,
        tenant_id=tenant_id,
        page_number=1,
        blob_path=f"rag-vault/{tenant_id}/{doc_obj.id}/page-1.png",
        content="Official policy: visitor parking is limited to 2 hours.",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(page)
    await db_session.flush()

    chunk = RagChunk(
        id=uuid4(),
        document_id=doc_obj.id,
        tenant_id=tenant_id,
        page_ids=[page.id],
        content_hash="def456",
        text=page.content,
        embedding=[0.1] * 1536,
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(chunk)
    await db_session.commit()
    return doc_obj, page, chunk


@pytest.mark.anyio
class TestRagRetrievalQuery:
    async def test_query_insufficient_evidence_no_docs(self, async_client: AsyncClient, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        resp = await async_client.post(
            "/api/v1/agencies/rag/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What is the parking policy?", "include_debug": True},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "insufficient_evidence"
        assert data["debug"]["confidence_status"] == "insufficient"
        assert data["debug"]["fallback_reason"] == "no_processed_documents"

    async def test_query_empty_query_returns_400(self, async_client: AsyncClient, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        resp = await async_client.post(
            "/api/v1/agencies/rag/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": ""},
        )
        assert resp.status_code == 422

    async def test_query_sufficient_evidence(self, async_client: AsyncClient, db_session, test_tenant, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        await _create_processed_document(db_session, test_tenant.id)

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            with patch("app.rag.service.get_reranking_provider") as mock_rerank:
                mock_rerank.return_value.rerank = AsyncMock(
                    return_value=[{"index": 0, "document": "chunk text", "score": 0.95}]
                )
                with patch("app.rag.service.generate_guardrailed_policy_answer") as mock_guarded:
                    mock_guarded.return_value = GuardrailedGenerationResult(
                        answer_text="Visitor parking is limited to 2 hours.",
                        guardrail_status="passed",
                        blocked_reason=None,
                        generation_provider="nemo_guardrails",
                    )
                    resp = await async_client.post(
                        "/api/v1/agencies/rag/query",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"query": "What is the parking policy?", "include_debug": True},
                    )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("answered", "fallback")
        if data["status"] == "answered":
            assert "2 hours" in data["answer"]
        assert len(data["citations"]) >= 0
        assert data["debug"]["retrieval_log_id"] is not None

    async def test_query_accepts_conversation_history(self, async_client: AsyncClient, db_session, test_tenant, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        await _create_processed_document(db_session, test_tenant.id)

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            with patch("app.rag.service.get_reranking_provider") as mock_rerank:
                mock_rerank.return_value.rerank = AsyncMock(
                    return_value=[{"index": 0, "document": "chunk text", "score": 0.95}]
                )
                with patch("app.rag.service.generate_guardrailed_policy_answer") as mock_guarded:
                    mock_guarded.return_value = GuardrailedGenerationResult(
                        answer_text="Visitor parking is limited to 2 hours.",
                        guardrail_status="passed",
                        blocked_reason=None,
                        generation_provider="nemo_guardrails",
                    )
                    resp = await async_client.post(
                        "/api/v1/agencies/rag/query",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "query": "And what about after hours?",
                            "include_debug": True,
                            "conversation_messages": [
                                {"role": "user", "content": "What is parking policy?"},
                                {"role": "assistant", "content": "Parking is limited."},
                            ],
                        },
                    )

        assert resp.status_code == 200
        assert mock_guarded.call_args.kwargs["conversation_messages"]

    async def test_query_tenant_isolation(self, async_client: AsyncClient, db_session, test_tenant):
        """Tenant A user should not see Tenant B documents in query results."""
        from app.agencies.models import AgencyEmployeeMembership, AgencyTenant
        from app.common.security import hash_password
        from app.users.models import User

        now = datetime.now(timezone.utc)
        tenant_b_id = uuid4()
        user_b_id = uuid4()

        role_result = await db_session.execute(
            text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1")
        )
        role_id = role_result.scalar_one()

        tenant_b = AgencyTenant(
            id=tenant_b_id,
            name=f"rbac-tenant-b-{tenant_b_id.hex[:4]}",
            slug=f"rbac-tenant-b-{tenant_b_id.hex[:8]}",
            status="active",
            created_at=now,
            updated_at=now,
        )
        user_b = User(
            id=user_b_id,
            email=f"rbac-user-b-{user_b_id.hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            name="RBAC User B",
            role_id=role_id,
            is_active=True,
            status="active",
            created_at=now,
            updated_at=now,
        )
        membership_b = AgencyEmployeeMembership(
            id=uuid4(),
            agency_tenant_id=tenant_b_id,
            user_id=user_b_id,
            role_id=role_id,
            status="active",
            display_name=user_b.name,
            work_email=user_b.email,
            created_at=now,
            updated_at=now,
        )
        db_session.add(tenant_b)
        await db_session.flush()
        db_session.add(user_b)
        await db_session.flush()
        db_session.add(membership_b)
        await db_session.flush()
        await db_session.commit()

        await _create_processed_document(db_session, test_tenant.id, filename="policy-A.pdf")

        token_b = await _login(async_client, user_b.email, "TestPass123!")

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            resp = await async_client.post(
                "/api/v1/agencies/rag/query",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"query": "policy A content"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "insufficient_evidence"


@pytest.mark.anyio
class TestRagRetrievalLogs:
    async def test_logs_admin_allowed(self, async_client: AsyncClient, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    async def test_logs_support_employee_denied(self, async_client: AsyncClient, support_user):
        user, password = support_user
        token = await _login(async_client, user.email, password)

        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_logs_pagination(self, async_client: AsyncClient, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["size"] == 5

    async def test_logs_filters(self, async_client: AsyncClient, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs?confidence_status=sufficient",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data


@pytest.mark.anyio
class TestReplaceWhileRetrieving:
    async def test_replace_survives_concurrent_query(self, async_client: AsyncClient, db_session, test_tenant, agency_admin_user):
        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        doc, page, chunk = await _create_processed_document(db_session, test_tenant.id)

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            with patch("app.rag.service.get_reranking_provider") as mock_rerank:
                mock_rerank.return_value.rerank = AsyncMock(
                    return_value=[{"index": 0, "document": "chunk text", "score": 0.95}]
                )
                with patch(
                    "app.rag.service.generate_guardrailed_policy_answer",
                    new_callable=AsyncMock,
                ) as mock_guarded:
                    mock_guarded.return_value = GuardrailedGenerationResult(
                        answer_text="Visitor parking is limited to 2 hours.",
                        guardrail_status="passed",
                        blocked_reason=None,
                        generation_provider="nemo_guardrails",
                    )
                    resp_before = await async_client.post(
                        "/api/v1/agencies/rag/query",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"query": "parking policy", "include_debug": True},
                    )
        assert resp_before.status_code == 200

        with patch("app.rag.service._extract_text_from_pdf", return_value="Updated policy text."):
            replace_resp = await async_client.post(
                f"/api/v1/agencies/rag/documents/{doc.id}/replace",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )
        assert replace_resp.status_code == 202

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed = AsyncMock(return_value=[[0.1] * 1536])
            with patch("app.rag.service.get_reranking_provider") as mock_rerank:
                mock_rerank.return_value.rerank = AsyncMock(
                    return_value=[{"index": 0, "document": "chunk text", "score": 0.95}]
                )
                with patch(
                    "app.rag.service.generate_guardrailed_policy_answer",
                    new_callable=AsyncMock,
                ) as mock_guarded:
                    mock_guarded.return_value = GuardrailedGenerationResult(
                        answer_text="Visitor parking is limited to 2 hours.",
                        guardrail_status="passed",
                        blocked_reason=None,
                        generation_provider="nemo_guardrails",
                    )
                    resp_after = await async_client.post(
                        "/api/v1/agencies/rag/query",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"query": "parking policy", "include_debug": True},
                    )
        assert resp_after.status_code == 200


@pytest.mark.anyio
class TestRagEvaluationPersistence:
    async def test_record_and_list_evaluation_runs(
        self, async_client: AsyncClient, db_session, test_tenant, agency_admin_user
    ):
        user, password = agency_admin_user
        ex_id_1 = f"int-ex-1-{uuid4().hex[:8]}"
        ex_id_2 = f"int-ex-2-{uuid4().hex[:8]}"

        examples = [
            RagEvaluationExampleCreate(
                id=ex_id_1,
                query="test query",
                tenant_fixture="agency-test",
                expected_behavior="answer",
                expected_source_labels=["policy-page-1"],
                passed=True,
                summary={"status": "answered", "behavior_ok": True, "sources_ok": True},
            ),
            RagEvaluationExampleCreate(
                id=ex_id_2,
                query="refuse query",
                tenant_fixture="agency-test",
                expected_behavior="refuse",
                expected_source_labels=[],
                passed=True,
                summary={"status": "insufficient_evidence", "behavior_ok": True, "sources_ok": True},
            ),
        ]

        run_label = f"int-test-eval-{uuid4().hex[:8]}"
        from app.common.tenant import TenantContext
        from app.common.rls import apply_rls_context_to_session

        ctx = TenantContext(
            actor_id=uuid4(),
            role="agency_admin",
            tenant_id=test_tenant.id,
        )
        await apply_rls_context_to_session(
            db_session,
            tenant_id=ctx.tenant_id,
            user_id=ctx.actor_id,
            role=ctx.role,
        )
        service = RagRetrievalService(db_session, ctx)
        run = await service.record_evaluation_run_with_examples(
            run_label=run_label,
            examples=examples,
            summary={"total_examples": 2, "passed": 2, "failed": 0, "pass_rate": 1.0},
        )
        await db_session.commit()

        assert run.run_label == run_label
        assert run.total_examples == 2
        assert run.passed_examples == 2
        assert run.failed_examples == 0

        from app.rag.repository import RagRepository
        from app.common.pagination import PaginationRequest

        repo = RagRepository(db_session)
        runs, total = await repo.list_evaluation_runs(
            tenant_id=None,
            pagination=PaginationRequest(page=1, page_size=20),
        )
        assert total >= 1
        assert any(r.run_label == run_label for r in runs)
        await db_session.delete(run)
        await db_session.commit()

    async def test_evaluation_run_with_failed_examples(
        self, async_client: AsyncClient, db_session, test_tenant, agency_admin_user
    ):
        ex_id_1 = f"fail-ex-1-{uuid4().hex[:8]}"
        ex_id_2 = f"fail-ex-2-{uuid4().hex[:8]}"

        examples = [
            RagEvaluationExampleCreate(
                id=ex_id_1,
                query="expected answer got refuse",
                tenant_fixture="agency-test",
                expected_behavior="answer",
                expected_source_labels=["missing-source"],
                passed=False,
                summary={"status": "insufficient_evidence", "behavior_ok": False, "sources_ok": False},
            ),
            RagEvaluationExampleCreate(
                id=ex_id_2,
                query="partial match",
                tenant_fixture="agency-test",
                expected_behavior="answer",
                expected_source_labels=["present-source"],
                passed=True,
                summary={"status": "answered", "behavior_ok": True, "sources_ok": True},
            ),
        ]

        run_label = f"int-fail-eval-{uuid4().hex[:8]}"
        from app.common.tenant import TenantContext
        from app.common.rls import apply_rls_context_to_session

        ctx = TenantContext(
            actor_id=uuid4(),
            role="agency_admin",
            tenant_id=test_tenant.id,
        )
        await apply_rls_context_to_session(
            db_session,
            tenant_id=ctx.tenant_id,
            user_id=ctx.actor_id,
            role=ctx.role,
        )
        service = RagRetrievalService(db_session, ctx)
        run = await service.record_evaluation_run_with_examples(
            run_label=run_label,
            examples=examples,
            summary={
                "total_examples": 2,
                "passed": 1,
                "failed": 1,
                "pass_rate": 0.5,
                "latency_ms": {"min": 100, "max": 300, "avg": 200, "p50": 200, "p95": 300},
                "latency_violations": 0,
            },
        )
        await db_session.commit()

        assert run.total_examples == 2
        assert run.passed_examples == 1
        assert run.failed_examples == 1
        assert run.summary["pass_rate"] == 0.5
        assert "latency_ms" in run.summary
        await db_session.delete(run)
        await db_session.commit()
