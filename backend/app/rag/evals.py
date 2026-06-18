from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agencies.models import AgencyEmployeeMembership, AgencyTenant
from app.ai.azure_openai import _normalize_azure_base_url
from app.ai.registry import get_embedding_provider
from app.auth.models import Role
from app.common.config import settings
from app.common.rls import apply_rls_context_to_session
from app.common.security import hash_password
from app.common.tenant import TenantContext
from app.rag.models import RagChunk, RagDocument, RagPage
from app.rag.schemas import RagEvaluationExampleCreate, RagPolicyAnswer, RagRetrievalQueryRequest
from app.rag.service import RagRetrievalService
from app.users.models import User


APP_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = APP_ROOT / "tests" / "fixtures" / "rag_eval"
DEFAULT_DATASET_PATH = FIXTURE_ROOT / "policy_retrieval_ragas.jsonl"
DEFAULT_MANIFEST_PATH = FIXTURE_ROOT / "fixture_manifest.json"
PAGE_DELIMITER = "\n=== PAGE BREAK ===\n"
BLOCKING_MODE = "blocking"
MANUAL_MODE = "manual"
BLOCKING_EXAMPLE_COUNT = 20
MANUAL_EXAMPLE_COUNT = 40
DEFAULT_TOP_K = 5
DEFAULT_LATENCY_MAX_MS = 15000

THRESHOLDS = {
    "faithfulness": 0.70,
    "context_precision": 0.65,
    "context_recall": 0.65,
    "answer_relevancy": 0.65,
    "hit_at_1": 0.60,
    "hit_at_5": 0.90,
    "tenant_leakage_count": 0,
    "p95_latency_ms": DEFAULT_LATENCY_MAX_MS,
}


@contextmanager
def _eval_runtime_overrides():
    original_guardrails_enabled = settings.ai_guardrails_enabled
    original_nemo_runtime = settings.ai_guardrails_use_nemo_runtime
    original_content_safety_model = settings.openrouter_content_safety_model
    try:
        # Live RAGAS runs should evaluate the RAG answering path with the Azure judge.
        # OpenRouter content safety sits on the app runtime path and can rate-limit the
        # harness independently of the actual eval provider, which makes results noisy.
        settings.ai_guardrails_enabled = False
        settings.ai_guardrails_use_nemo_runtime = False
        settings.openrouter_content_safety_model = ""
        yield
    finally:
        settings.ai_guardrails_enabled = original_guardrails_enabled
        settings.ai_guardrails_use_nemo_runtime = original_nemo_runtime
        settings.openrouter_content_safety_model = original_content_safety_model


@dataclass(slots=True)
class EvalExample:
    id: str
    query: str
    tenant_fixture: str
    expected_behavior: str
    reference_answer: str
    expected_source_labels: list[str]
    expect_tenant_leakage: bool
    evaluation_mode: str
    notes: str | None = None


@dataclass(slots=True)
class SeededTenantFixture:
    tenant_id: UUID
    actor_user_id: UUID
    tenant_fixture: str
    document_ids: set[UUID]
    document_labels: set[str]


def _jsonl_lines(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _resolve_path(path: Path) -> Path:
    if path.is_absolute() or path.exists():
        return path
    candidate = APP_ROOT / path
    if candidate.exists():
        return candidate
    return path


def load_eval_examples(path: Path = DEFAULT_DATASET_PATH, mode: str = BLOCKING_MODE) -> list[EvalExample]:
    if mode not in {BLOCKING_MODE, MANUAL_MODE}:
        raise ValueError(f"Unsupported evaluation mode: {mode}")

    records = [EvalExample(**row) for row in _jsonl_lines(_resolve_path(path))]
    if mode == BLOCKING_MODE:
        filtered = [record for record in records if record.evaluation_mode == BLOCKING_MODE]
        if len(filtered) != BLOCKING_EXAMPLE_COUNT:
            raise ValueError(
                f"Blocking dataset must contain exactly {BLOCKING_EXAMPLE_COUNT} examples; found {len(filtered)}"
            )
        return filtered

    if len(records) != MANUAL_EXAMPLE_COUNT:
        raise ValueError(
            f"Manual dataset must contain exactly {MANUAL_EXAMPLE_COUNT} examples; found {len(records)}"
        )
    return records


def load_fixture_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    resolved = _resolve_path(path)
    with resolved.open(encoding="utf-8") as handle:
        return json.load(handle)


def _hash_text(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


def _latency_stats(latencies_ms: list[float]) -> dict[str, float]:
    if not latencies_ms:
        return {"min": 0.0, "max": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0}

    sorted_values = sorted(latencies_ms)
    return {
        "min": round(sorted_values[0], 1),
        "max": round(sorted_values[-1], 1),
        "avg": round(sum(sorted_values) / len(sorted_values), 1),
        "p50": round(statistics.median(sorted_values), 1),
        "p95": round(sorted_values[min(len(sorted_values) - 1, math.ceil(len(sorted_values) * 0.95) - 1)], 1),
    }


def _clean_metric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric):
        return None
    return numeric


def _result_rows(eval_result: Any) -> list[dict[str, Any]]:
    if hasattr(eval_result, "to_pandas"):
        dataframe = eval_result.to_pandas()
        return dataframe.to_dict(orient="records")
    if hasattr(eval_result, "scores"):
        return list(eval_result.scores)
    raise RuntimeError("Unsupported RAGAS EvaluationResult shape")


def _behavior_ok(expected_behavior: str, answer: RagPolicyAnswer) -> bool:
    if expected_behavior == "answer":
        return answer.status in {"answered", "fallback"}
    if expected_behavior == "refuse":
        return answer.status == "insufficient_evidence"
    return False


def _hit_at_k(actual_labels: list[str], expected_labels: set[str], limit: int) -> bool:
    if not expected_labels:
        return False
    return any(label in expected_labels for label in actual_labels[:limit])


def _find_tenant_leakage(
    answer: RagPolicyAnswer,
    fixtures: dict[str, SeededTenantFixture],
    tenant_fixture: str,
) -> tuple[bool, list[str]]:
    allowed_ids = fixtures[tenant_fixture].document_ids
    leaked_sources: list[str] = []
    for evidence in answer.evidence:
        if evidence.document_id not in allowed_ids:
            leaked_sources.append(evidence.source_label)
    return bool(leaked_sources), leaked_sources


def _threshold_pass(metric_name: str, value: float | int | None) -> bool:
    if value is None:
        return False
    threshold = THRESHOLDS[metric_name]
    if metric_name == "tenant_leakage_count":
        return int(value) == int(threshold)
    return float(value) >= float(threshold)


def summarize_results(
    *,
    examples: list[EvalExample],
    answers: list[RagPolicyAnswer],
    latencies_ms: list[float],
    fixtures: dict[str, SeededTenantFixture],
    ragas_rows: list[dict[str, Any]],
    judge_errors: list[str],
) -> tuple[list[RagEvaluationExampleCreate], dict[str, Any]]:
    ragas_metric_fields = ("faithfulness", "context_precision", "context_recall", "answer_relevancy")
    answerable_examples = [example for example in examples if example.expected_behavior == "answer"]
    ragas_by_example = {
        example.id: ragas_rows[index] if index < len(ragas_rows) else {}
        for index, example in enumerate(answerable_examples)
    }

    persisted_examples: list[RagEvaluationExampleCreate] = []
    metric_values: dict[str, list[float]] = {field: [] for field in ragas_metric_fields}
    hit_1_total = 0
    hit_5_total = 0
    expected_source_match_total = 0
    tenant_leakage_examples: list[str] = []

    for index, example in enumerate(examples):
        answer = answers[index]
        latency_ms = latencies_ms[index]
        expected_labels = set(example.expected_source_labels)
        actual_labels = [evidence.source_label for evidence in answer.evidence]
        behavior_ok = _behavior_ok(example.expected_behavior, answer)
        hit_at_1 = _hit_at_k(actual_labels, expected_labels, 1)
        hit_at_5 = _hit_at_k(actual_labels, expected_labels, 5)
        expected_source_match = expected_labels.issubset(set(actual_labels))
        leaked, leaked_sources = _find_tenant_leakage(answer, fixtures, example.tenant_fixture)
        if leaked:
            tenant_leakage_examples.append(example.id)

        ragas_scores = ragas_by_example.get(example.id, {})
        cleaned_scores = {field: _clean_metric(ragas_scores.get(field)) for field in ragas_metric_fields}
        if example.expected_behavior == "answer":
            for field, score in cleaned_scores.items():
                if score is not None:
                    metric_values[field].append(score)
            hit_1_total += int(hit_at_1)
            hit_5_total += int(hit_at_5)
            expected_source_match_total += int(expected_source_match)

        threshold_violations: list[str] = []
        if not behavior_ok:
            threshold_violations.append("behavior")
        if leaked:
            threshold_violations.append("tenant_leakage")
        if example.expected_behavior == "answer":
            if not hit_at_1:
                threshold_violations.append("hit_at_1")
            if not hit_at_5:
                threshold_violations.append("hit_at_5")
            for field, score in cleaned_scores.items():
                if not _threshold_pass(field, score):
                    threshold_violations.append(field)

        passed = not threshold_violations
        persisted_examples.append(
            RagEvaluationExampleCreate(
                id=f"placeholder-{example.id}",
                query=example.query,
                tenant_fixture=example.tenant_fixture,
                expected_behavior=example.expected_behavior,
                expected_source_labels=example.expected_source_labels,
                notes=example.notes,
                passed=passed,
                summary={
                    "dataset_example_id": example.id,
                    "reference_answer": example.reference_answer,
                    "answer_status": answer.status,
                    "behavior_ok": behavior_ok,
                    "expected_sources": example.expected_source_labels,
                    "actual_sources": actual_labels,
                    "latency_ms": round(latency_ms, 1),
                    "hit_at_1": hit_at_1 if example.expected_behavior == "answer" else None,
                    "hit_at_5": hit_at_5 if example.expected_behavior == "answer" else None,
                    "expected_source_match": expected_source_match if example.expected_behavior == "answer" else None,
                    "tenant_leakage": leaked,
                    "tenant_leakage_sources": leaked_sources,
                    "ragas": cleaned_scores if example.expected_behavior == "answer" else {"skipped_reason": "refusal_case"},
                    "threshold_violations": threshold_violations,
                    "retrieval_log_id": str(answer.debug.retrieval_log_id) if answer.debug else None,
                },
            )
        )

    answerable_count = len(answerable_examples)
    aggregate_metrics = {
        field: round(sum(values) / len(values), 4) if values else None
        for field, values in metric_values.items()
    }
    hit_at_1_score = round(hit_1_total / answerable_count, 4) if answerable_count else None
    hit_at_5_score = round(hit_5_total / answerable_count, 4) if answerable_count else None
    expected_source_match_rate = (
        round(expected_source_match_total / answerable_count, 4) if answerable_count else None
    )

    summary = {
        "total_examples": len(examples),
        "answerable_examples": answerable_count,
        "refusal_examples": len(examples) - answerable_count,
        "judge_failures": len(judge_errors),
        "judge_errors": judge_errors,
        "metrics": {
            **aggregate_metrics,
            "hit_at_1": hit_at_1_score,
            "hit_at_5": hit_at_5_score,
            "expected_source_match_rate": expected_source_match_rate,
            "tenant_leakage_count": len(tenant_leakage_examples),
            "tenant_leakage_examples": tenant_leakage_examples,
        },
        "latency_ms": _latency_stats(latencies_ms),
        "thresholds": THRESHOLDS,
    }
    return persisted_examples, summary


def enforce_thresholds(summary: dict[str, Any], *, allow_judge_failures: bool = False) -> list[str]:
    failures: list[str] = []
    metrics = summary["metrics"]
    latency_ms = summary["latency_ms"]

    for metric_name in ("faithfulness", "context_precision", "context_recall", "answer_relevancy", "hit_at_1", "hit_at_5"):
        if not _threshold_pass(metric_name, metrics.get(metric_name)):
            failures.append(metric_name)

    if not _threshold_pass("tenant_leakage_count", metrics.get("tenant_leakage_count")):
        failures.append("tenant_leakage_count")

    if latency_ms.get("p95", 0.0) > THRESHOLDS["p95_latency_ms"]:
        failures.append("p95_latency_ms")

    if summary.get("judge_failures", 0) and not allow_judge_failures:
        failures.append("judge_failures")

    return failures


def _require_azure_eval_config() -> None:
    missing = [
        name
        for name, value in {
            "AZURE_OPENAI_ENDPOINT": settings.azure_openai_endpoint,
            "AZURE_OPENAI_API_KEY": settings.azure_openai_api_key,
            "AZURE_OPENAI_CHAT_DEPLOYMENT": settings.azure_openai_chat_deployment,
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": settings.azure_openai_embedding_deployment,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Azure judge config: {', '.join(missing)}")


def _build_ragas_models() -> tuple[Any, Any]:
    _require_azure_eval_config()
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    base_url = _normalize_azure_base_url(settings.azure_openai_endpoint)
    llm = ChatOpenAI(
        model=settings.azure_openai_chat_deployment,
        api_key=settings.azure_openai_api_key,
        base_url=base_url,
        temperature=0.0,
        timeout=120,
        max_retries=2,
    )
    embeddings = OpenAIEmbeddings(
        model=settings.azure_openai_embedding_deployment,
        api_key=settings.azure_openai_api_key,
        base_url=base_url,
        max_retries=2,
    )
    return llm, embeddings


def _build_ragas_dataset(rows: list[dict[str, Any]]) -> Any:
    from datasets import Dataset

    return Dataset.from_list(rows)


def _get_ragas_metrics() -> list[Any]:
    from ragas.metrics import context_precision, context_recall, faithfulness

    try:
        from ragas.metrics import answer_relevancy
    except ImportError:  # pragma: no cover
        from ragas.metrics import response_relevancy as answer_relevancy

    return [faithfulness, context_precision, context_recall, answer_relevancy]


async def evaluate_with_ragas(
    rows: list[dict[str, Any]],
    *,
    allow_failures: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not rows:
        return [], []

    try:
        os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
        from ragas import evaluate

        llm, embeddings = _build_ragas_models()
        dataset = _build_ragas_dataset(rows)
        result = evaluate(
            dataset=dataset,
            metrics=_get_ragas_metrics(),
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=False,
            show_progress=False,
        )
    except Exception as exc:
        if not allow_failures:
            raise
        return [], [f"RAGAS judge unavailable: {exc}"]

    raw_rows = _result_rows(result)
    judge_errors: list[str] = []
    for row in raw_rows:
        missing_score = any(
            _clean_metric(row.get(field)) is None
            for field in ("faithfulness", "context_precision", "context_recall", "answer_relevancy")
        )
        if missing_score:
            judge_errors.append(f"RAGAS row missing score for question: {row.get('question', '<unknown>')}")
    return raw_rows, judge_errors


async def _lookup_role_id(session: AsyncSession, role_slug: str) -> UUID:
    result = await session.execute(select(Role.id).where(Role.slug == role_slug))
    role_id = result.scalar_one_or_none()
    if role_id is None:
        raise RuntimeError(f"Missing role slug: {role_slug}")
    return role_id


async def _cleanup_prior_fixtures(session: AsyncSession) -> None:
    result = await session.execute(select(AgencyTenant.id).where(AgencyTenant.slug.like("ragas-fixture-%")))
    tenant_ids = list(result.scalars().all())
    if not tenant_ids:
        return
    await session.execute(delete(AgencyTenant).where(AgencyTenant.id.in_(tenant_ids)))
    await session.commit()


async def seed_fixture_tenants(
    session: AsyncSession,
    manifest: dict[str, Any],
) -> dict[str, SeededTenantFixture]:
    await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)
    await _cleanup_prior_fixtures(session)
    await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)
    role_id = await _lookup_role_id(session, "agency_admin")
    embedding_provider = get_embedding_provider()

    fixtures: dict[str, SeededTenantFixture] = {}
    for tenant_spec in manifest["tenants"]:
        tenant_fixture = tenant_spec["tenant_fixture"]
        tenant_id = uuid4()
        user_id = uuid4()
        tenant = AgencyTenant(
            id=tenant_id,
            name=tenant_spec["name"],
            slug=f"ragas-fixture-{tenant_fixture}-{tenant_id.hex[:8]}",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        user = User(
            id=user_id,
            email=f"ragas-{tenant_fixture}-{user_id.hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            name=f"RAGAS {tenant_fixture}",
            role_id=role_id,
            is_active=True,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        membership = AgencyEmployeeMembership(
            id=uuid4(),
            agency_tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
            status="active",
            display_name=user.name,
            work_email=user.email,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(tenant)
        await session.flush()
        session.add(user)
        await session.flush()
        session.add(membership)
        await session.flush()

        allowed_document_ids: set[UUID] = set()
        allowed_labels: set[str] = set()

        for document_spec in tenant_spec["documents"]:
            filename = document_spec["filename"]
            source_path = FIXTURE_ROOT / document_spec["source_path"]
            content = source_path.read_text(encoding="utf-8")
            page_texts = [page.strip() for page in content.split(PAGE_DELIMITER) if page.strip()]
            embeddings = await embedding_provider.embed(page_texts)

            document_id = uuid4()
            document = RagDocument(
                id=document_id,
                tenant_id=tenant_id,
                filename=filename,
                status="processed",
                blob_path=f"rag-fixtures/{tenant_id}/{document_id}/{filename}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(document)
            await session.flush()

            for page_number, page_text in enumerate(page_texts, start=1):
                page_id = uuid4()
                page = RagPage(
                    id=page_id,
                    document_id=document_id,
                    tenant_id=tenant_id,
                    page_number=page_number,
                    blob_path=f"rag-fixtures/{tenant_id}/{document_id}/page-{page_number}.txt",
                    content=page_text,
                    created_at=datetime.now(timezone.utc),
                )
                chunk = RagChunk(
                    id=uuid4(),
                    document_id=document_id,
                    tenant_id=tenant_id,
                    page_ids=[page_id],
                    content_hash=_hash_text(f"{filename}:{page_number}:{page_text}"),
                    text=page_text,
                    embedding=embeddings[page_number - 1],
                    status="active",
                    created_at=datetime.now(timezone.utc),
                )
                session.add_all([page, chunk])
                allowed_labels.add(f"{filename} p.{page_number}")

            allowed_document_ids.add(document_id)

        fixtures[tenant_fixture] = SeededTenantFixture(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            tenant_fixture=tenant_fixture,
            document_ids=allowed_document_ids,
            document_labels=allowed_labels,
        )

    await session.commit()
    return fixtures


async def run_eval(
    session_factory: Any,
    *,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    mode: str = BLOCKING_MODE,
    top_k: int = DEFAULT_TOP_K,
    run_label: str | None = None,
    allow_judge_failures: bool = False,
) -> dict[str, Any]:
    examples = load_eval_examples(dataset_path, mode)
    manifest = load_fixture_manifest(manifest_path)
    run_label = run_label or f"ragas-{mode}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    if any(example.expected_behavior == "answer" for example in examples) and not allow_judge_failures:
        _require_azure_eval_config()

    async with session_factory() as seed_session:
        fixtures = await seed_fixture_tenants(seed_session, manifest)

    answers: list[RagPolicyAnswer] = []
    latencies_ms: list[float] = []
    ragas_input_rows: list[dict[str, Any]] = []

    with _eval_runtime_overrides():
        for example in examples:
            fixture = fixtures[example.tenant_fixture]
            async with session_factory() as query_session:
                await apply_rls_context_to_session(
                    query_session,
                    tenant_id=fixture.tenant_id,
                    user_id=fixture.actor_user_id,
                    role="agency_admin",
                )
                service = RagRetrievalService(
                    query_session,
                    TenantContext(
                        actor_id=fixture.actor_user_id,
                        role="agency_admin",
                        tenant_id=fixture.tenant_id,
                    ),
                )
                start = time.monotonic()
                answer = await service.answer_policy_query(
                    RagRetrievalQueryRequest(query=example.query, top_k=top_k, include_debug=True)
                )
                latency_ms = (time.monotonic() - start) * 1000
                answers.append(answer)
                latencies_ms.append(latency_ms)

            if example.expected_behavior == "answer":
                ragas_input_rows.append(
                    {
                        "question": example.query,
                        "answer": answer.answer,
                        "ground_truth": example.reference_answer,
                        "contexts": [evidence.parent_page_text or evidence.text_preview for evidence in answer.evidence],
                    }
                )

    ragas_rows, judge_errors = await evaluate_with_ragas(
        ragas_input_rows,
        allow_failures=allow_judge_failures,
    )
    persisted_examples, summary = summarize_results(
        examples=examples,
        answers=answers,
        latencies_ms=latencies_ms,
        fixtures=fixtures,
        ragas_rows=ragas_rows,
        judge_errors=judge_errors,
    )

    for example in persisted_examples:
        dataset_example_id = example.summary["dataset_example_id"]
        example.id = f"{run_label}:{dataset_example_id}"

    threshold_failures = enforce_thresholds(summary, allow_judge_failures=allow_judge_failures)
    summary["threshold_failures"] = threshold_failures
    summary["run_label"] = run_label
    summary["mode"] = mode

    first_fixture = next(iter(fixtures.values()))
    async with session_factory() as persist_session:
        await apply_rls_context_to_session(
            persist_session,
            tenant_id=first_fixture.tenant_id,
            user_id=first_fixture.actor_user_id,
            role="agency_admin",
        )
        service = RagRetrievalService(
            persist_session,
            TenantContext(
                actor_id=first_fixture.actor_user_id,
                role="agency_admin",
                tenant_id=first_fixture.tenant_id,
            ),
        )
        run = await service.record_evaluation_run_with_examples(
            run_label=run_label,
            examples=persisted_examples,
            summary=summary,
        )

    return {
        "run": run,
        "summary": summary,
        "examples": persisted_examples,
    }
