from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app.admin.service import PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE
from app.common.cache import cache_invalidate_namespace
from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session
from app.rag.models import RagEvaluationExample, RagEvaluationRun
from httpx import AsyncClient

PLATFORM_ADMIN_EMAIL = "platform.admin@akarai.test"
AGENCY_ADMIN_EMAIL = "agency.admin@akarai.test"


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _save_records(*records) -> None:
    await cache_invalidate_namespace(PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE)
    async with async_session_factory() as session:
        if not session.in_transaction():
            await session.begin()
        await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)
        for record in records:
            session.add(record)
            await session.flush()
        await session.commit()


async def _delete_records(*records) -> None:
    async with async_session_factory() as session:
        if not session.in_transaction():
            await session.begin()
        await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)
        for record in records:
            merged = await session.merge(record)
            await session.delete(merged)
        await session.commit()
    await cache_invalidate_namespace(PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE)


@pytest.mark.anyio
class TestPlatformRagEvalsAPI:
    @pytest.mark.integration
    async def test_platform_admin_can_list_runs(self, async_client: AsyncClient):
        run = RagEvaluationRun(
            id=uuid4(),
            run_label="ragas-blocking-test",
            completed_at=datetime.now(timezone.utc),
            total_examples=20,
            passed_examples=19,
            failed_examples=1,
            summary={
                "mode": "blocking",
                "judge_failures": 0,
                "threshold_failures": [],
                "metrics": {"faithfulness": 0.8, "hit_at_5": 1.0, "tenant_leakage_count": 0},
                "latency_ms": {"p95": 2000},
            },
        )
        await _save_records(run)
        try:
            token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
            resp = await async_client.get(
                "/api/v1/platform/rag-evals/runs",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["items"]
            match = next(item for item in data["items"] if item["run_id"] == str(run.id))
            assert match["mode"] == "blocking"
            assert match["faithfulness"] == 0.8
            assert match["hit_at_5"] == 1.0
        finally:
            await _delete_records(run)

    @pytest.mark.integration
    async def test_platform_admin_can_get_run_detail(self, async_client: AsyncClient):
        run = RagEvaluationRun(
            id=uuid4(),
            run_label="ragas-manual-test",
            completed_at=datetime.now(timezone.utc),
            total_examples=40,
            passed_examples=38,
            failed_examples=2,
            summary={
                "mode": "manual",
                "judge_failures": 0,
                "threshold_failures": ["context_precision"],
                "metrics": {"context_precision": 0.5, "hit_at_5": 0.9, "tenant_leakage_count": 0},
                "latency_ms": {"p95": 2400},
            },
        )
        example = RagEvaluationExample(
            id="example-1",
            run_id=run.id,
            query="What is the PTO policy?",
            tenant_fixture="tenant_a",
            expected_behavior="answer",
            passed=False,
            summary={
                "latency_ms": 1234.5,
                "failure_reasons": ["context_precision"],
                "answer": {"status": "answered"},
                "metrics": {"context_precision": 0.4, "hit_at_5": True},
            },
        )
        await _save_records(run)
        await _save_records(example)
        try:
            token = await _login(async_client, PLATFORM_ADMIN_EMAIL)
            resp = await async_client.get(
                f"/api/v1/platform/rag-evals/runs/{run.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["run"]["run_id"] == str(run.id)
            assert data["run"]["mode"] == "manual"
            assert data["examples"][0]["example_id"] == "example-1"
            assert data["examples"][0]["answer_status"] == "answered"
        finally:
            await _delete_records(example, run)

    @pytest.mark.integration
    async def test_agency_admin_is_forbidden(self, async_client: AsyncClient):
        token = await _login(async_client, AGENCY_ADMIN_EMAIL)
        resp = await async_client.get(
            "/api/v1/platform/rag-evals/runs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
