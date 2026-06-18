from __future__ import annotations

import os
import socket
import sys
import types
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from app.common.config import settings
from app.common.database import async_session_factory
from app.rag.evals import (
    BLOCKING_MODE,
    MANUAL_MODE,
    EvalExample,
    enforce_thresholds,
    evaluate_with_ragas,
    load_eval_examples,
    load_fixture_manifest,
    run_eval,
    seed_fixture_tenants,
)
from app.rag.models import RagDocument, RagEvaluationExample, RagEvaluationRun
from app.rag.schemas import (
    RagPolicyAnswer,
    RagRetrievalCitation,
    RagRetrievalDebug,
    RagRetrievalEvidence,
)
from sqlalchemy import select
from sqlalchemy.engine import make_url

pytestmark = pytest.mark.anyio


class _DummyEmbeddingProvider:
    async def embed(self, texts, **kwargs):
        return [[0.1] * 1536 for _ in texts]


def _answer(
    *,
    status: str,
    answer_text: str,
    source_label: str = "tenant-a-operations.txt p.1",
) -> RagPolicyAnswer:
    return RagPolicyAnswer(
        status=status,
        answer=answer_text,
        citations=[
            RagRetrievalCitation(
                document_id="00000000-0000-0000-0000-000000000001",
                document_filename="tenant-a-operations.txt",
                page_number=1,
                source_label="tenant-a-operations.txt p.1",
            )
        ]
        if status != "insufficient_evidence"
        else [],
        evidence=[
            RagRetrievalEvidence(
                chunk_id="00000000-0000-0000-0000-000000000010",
                document_id="00000000-0000-0000-0000-000000000001",
                page_ids=["00000000-0000-0000-0000-000000000100"],
                document_filename="tenant-a-operations.txt",
                page_numbers=[1],
                source_label=source_label,
                vector_rank=1,
                vector_score=0.01,
                rerank_rank=1,
                rerank_score=0.99,
                text_preview="Visitor parking is limited to two hours.",
                parent_page_text="Visitor parking is limited to two hours and requires a dashboard permit.",
            )
        ]
        if status != "insufficient_evidence"
        else [],
        debug=RagRetrievalDebug(
            reranker_used=True,
            reranker_provider="openrouter",
            fallback_reason=None,
            confidence_status="sufficient" if status != "insufficient_evidence" else "insufficient",
            retrieval_log_id="00000000-0000-0000-0000-00000000abcd",
            vector_candidate_count=1 if status != "insufficient_evidence" else 0,
            rerank_candidate_count=1 if status != "insufficient_evidence" else 0,
        ),
    )


def _require_test_database() -> None:
    url = make_url(settings.database_url)
    host = url.host
    port = url.port or 5432
    try:
        socket.getaddrinfo(host, port)
    except OSError:
        pytest.skip(f"Test database host is unreachable from this environment: {host}:{port}")


def test_load_eval_examples_modes():
    blocking = load_eval_examples(mode=BLOCKING_MODE)
    manual = load_eval_examples(mode=MANUAL_MODE)

    assert len(blocking) == 20
    assert len(manual) == 40
    assert all(example.evaluation_mode == BLOCKING_MODE for example in blocking)


def test_enforce_thresholds_flags_failures():
    summary = {
        "judge_failures": 1,
        "metrics": {
            "faithfulness": 0.5,
            "context_precision": 0.9,
            "context_recall": 0.9,
            "answer_relevancy": 0.9,
            "hit_at_1": 0.5,
            "hit_at_5": 1.0,
            "tenant_leakage_count": 1,
        },
        "latency_ms": {"p95": 20000},
    }

    failures = enforce_thresholds(summary, allow_judge_failures=False)

    assert "faithfulness" in failures
    assert "hit_at_1" in failures
    assert "tenant_leakage_count" in failures
    assert "p95_latency_ms" in failures
    assert "judge_failures" in failures


@pytest.mark.parametrize(
    ("allow_failures", "raises", "expected_errors"),
    [
        (False, True, None),
        (True, False, ["RAGAS judge unavailable: boom"]),
    ],
)
async def test_evaluate_with_ragas_handles_judge_failures(allow_failures, raises, expected_errors):
    fake_ragas = types.ModuleType("ragas")
    fake_ragas.evaluate = lambda **kwargs: None
    with patch.dict(sys.modules, {"ragas": fake_ragas}):
        with patch("app.rag.evals._build_ragas_models", side_effect=RuntimeError("boom")):
            if raises:
                with pytest.raises(RuntimeError, match="boom"):
                    await evaluate_with_ragas(
                        [{"question": "q", "answer": "a", "ground_truth": "g", "contexts": ["c"]}],
                        allow_failures=allow_failures,
                    )
            else:
                rows, errors = await evaluate_with_ragas(
                    [{"question": "q", "answer": "a", "ground_truth": "g", "contexts": ["c"]}],
                    allow_failures=allow_failures,
                )
                assert rows == []
                assert errors == expected_errors


async def test_evaluate_with_ragas_sets_gitpython_refresh_guard():
    fake_ragas = types.ModuleType("ragas")
    fake_ragas.evaluate = lambda **kwargs: None
    with patch.dict(sys.modules, {"ragas": fake_ragas}):
        with patch.dict(os.environ, {}, clear=True):
            with patch("app.rag.evals._build_ragas_models", side_effect=RuntimeError("boom")):
                rows, errors = await evaluate_with_ragas(
                    [{"question": "q", "answer": "a", "ground_truth": "g", "contexts": ["c"]}],
                    allow_failures=True,
                )

    assert rows == []
    assert errors == ["RAGAS judge unavailable: boom"]
    assert os.environ["GIT_PYTHON_REFRESH"] == "quiet"


async def test_seed_fixture_tenants_creates_isolated_docs():
    _require_test_database()
    manifest = load_fixture_manifest()

    async with async_session_factory() as session:
        with patch("app.rag.evals.get_embedding_provider", return_value=_DummyEmbeddingProvider()):
            fixtures = await seed_fixture_tenants(session, manifest)

        assert set(fixtures.keys()) == {"agency-a", "agency-b"}
        assert all(len(fixture.document_ids) == 2 for fixture in fixtures.values())

        result = await session.execute(select(RagDocument))
        documents = list(result.scalars().all())
        fixture_doc_ids = set().union(*(fixture.document_ids for fixture in fixtures.values()))
        fixture_documents = [document for document in documents if document.id in fixture_doc_ids]
        assert len(fixture_documents) == 4
        assert {document.status for document in fixture_documents} == {"processed"}


async def test_run_eval_persists_results(tmp_path):
    _require_test_database()
    run_label = f"ragas-test-run-{uuid.uuid4().hex[:8]}"
    examples = [
        EvalExample(
            id="test-001",
            query="What is the visitor parking policy?",
            tenant_fixture="agency-a",
            expected_behavior="answer",
            reference_answer="Visitor parking is limited to two hours and requires a dashboard permit.",
            expected_source_labels=["tenant-a-operations.txt p.1"],
            expect_tenant_leakage=False,
            evaluation_mode=BLOCKING_MODE,
            notes="test",
        ),
        EvalExample(
            id="test-002",
            query="What is Blue Harbor's Harbor-Signal code phrase?",
            tenant_fixture="agency-a",
            expected_behavior="refuse",
            reference_answer="The assistant should refuse because there is not enough policy evidence.",
            expected_source_labels=[],
            expect_tenant_leakage=False,
            evaluation_mode=BLOCKING_MODE,
            notes="test",
        ),
    ]
    answers = [
        _answer(
            status="answered",
            answer_text="Visitor parking is limited to two hours and requires a dashboard permit.",
        ),
        _answer(
            status="insufficient_evidence",
            answer_text="I do not have enough policy evidence to answer that.",
        ),
    ]

    with patch("app.rag.evals.get_embedding_provider", return_value=_DummyEmbeddingProvider()):
        with patch("app.rag.evals.load_eval_examples", return_value=examples):
            with patch("app.rag.evals._find_tenant_leakage", return_value=(False, [])):
                with patch(
                    "app.rag.evals.evaluate_with_ragas",
                    new=AsyncMock(
                        return_value=(
                            [
                                {
                                    "question": "What is the visitor parking policy?",
                                    "faithfulness": 0.91,
                                    "context_precision": 0.88,
                                    "context_recall": 0.86,
                                    "answer_relevancy": 0.87,
                                }
                            ],
                            [],
                        )
                    ),
                ):
                    with patch("app.rag.evals._require_azure_eval_config", return_value=None):
                        with patch(
                            "app.rag.evals.RagRetrievalService.answer_policy_query",
                            new=AsyncMock(side_effect=answers),
                        ):
                            result = await run_eval(
                                async_session_factory,
                                mode=BLOCKING_MODE,
                                run_label=run_label,
                            )

    assert result["summary"]["metrics"]["faithfulness"] == 0.91
    assert result["summary"]["metrics"]["hit_at_1"] == 1.0
    assert result["summary"]["metrics"]["tenant_leakage_count"] == 0
    assert result["summary"]["threshold_failures"] == []

    async with async_session_factory() as session:
        run_result = await session.execute(
            select(RagEvaluationRun).where(RagEvaluationRun.run_label == run_label)
        )
        run = run_result.scalar_one()
        assert run.total_examples == 2

        example_result = await session.execute(
            select(RagEvaluationExample).where(RagEvaluationExample.run_id == run.id)
        )
        examples = list(example_result.scalars().all())
        assert len(examples) == 2
        assert all(example.id.startswith(f"{run_label}:") for example in examples)
        await session.delete(run)
        await session.commit()
