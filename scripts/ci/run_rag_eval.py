#!/usr/bin/env python3
"""
RAG Evaluation Baseline Runner

Loads the evaluation dataset, runs each query through the retrieval service,
scores the results, records latency, and persists the run + examples.

Usage (from backend container):
    python scripts/ci/run_rag_eval.py --tenant-id <uuid> [options]

Options:
    --tenant-id         UUID of the fixture tenant (required)
    --run-label         Optional label for the evaluation run
    --dataset           Path to evaluation dataset JSONL (default: backend/tests/fixtures/rag_eval/policy_retrieval_baseline.jsonl)
    --top-k             Number of chunks to retrieve per query (default: 8)
    --latency-max-ms    Maximum acceptable latency in ms (default: 5000)
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session
from app.common.tenant import TenantContext
from app.rag.schemas import RagEvaluationExampleCreate, RagRetrievalQueryRequest
from app.rag.service import RagRetrievalService


def load_dataset(path: str) -> list[dict]:
    examples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def score_example(result, expected_behavior: str, expected_source_labels: list[str]) -> tuple[bool, dict]:
    status = result.status

    if expected_behavior == "answer":
        behavior_ok = status in ("answered", "fallback")
    elif expected_behavior == "refuse":
        behavior_ok = status == "insufficient_evidence"
    else:
        behavior_ok = True

    actual_labels = [c.source_label for c in result.citations]
    sources_ok = (
        all(label in actual_labels for label in expected_source_labels)
        if expected_source_labels
        else True
    )

    passed = behavior_ok and sources_ok

    summary = {
        "status": status,
        "expected_behavior": expected_behavior,
        "behavior_ok": behavior_ok,
        "expected_sources": expected_source_labels,
        "actual_sources": actual_labels,
        "sources_ok": sources_ok,
        "confidence": result.debug.confidence_status if result.debug else None,
        "fallback_reason": result.debug.fallback_reason if result.debug else None,
    }
    return passed, summary


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG evaluation baseline")
    parser.add_argument("--tenant-id", type=str, required=True, help="UUID of the fixture tenant")
    parser.add_argument("--run-label", type=str, default=None, help="Optional label for the evaluation run")
    parser.add_argument(
        "--dataset",
        type=str,
        default="backend/tests/fixtures/rag_eval/policy_retrieval_baseline.jsonl",
        help="Path to evaluation dataset JSONL",
    )
    parser.add_argument("--top-k", type=int, default=8, help="Number of chunks to retrieve per query")
    parser.add_argument("--latency-max-ms", type=int, default=5000, help="Maximum acceptable latency in ms")
    args = parser.parse_args()

    tenant_id = UUID(args.tenant_id)
    run_label = args.run_label or f"eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)

    examples_data = load_dataset(str(dataset_path))
    print(f"Loaded {len(examples_data)} evaluation examples from {args.dataset}")

    ctx = TenantContext(
        actor_id=tenant_id,
        role="agency_admin",
        tenant_id=tenant_id,
    )

    latencies_ms: list[float] = []
    scored_examples: list[RagEvaluationExampleCreate] = []

    async with async_session_factory() as session:
        await apply_rls_context_to_session(
            session,
            tenant_id=ctx.tenant_id,
            user_id=ctx.actor_id,
            role=ctx.role,
        )

        service = RagRetrievalService(session, ctx)

        for i, ex in enumerate(examples_data):
            query = ex["query"]
            print(f"  [{i + 1}/{len(examples_data)}] {query[:60]}...", end=" ", flush=True)

            request = RagRetrievalQueryRequest(
                query=query,
                top_k=args.top_k,
                include_debug=True,
            )

            start = time.monotonic()
            try:
                result = await service.answer_policy_query(request)
            except Exception as exc:
                elapsed = (time.monotonic() - start) * 1000
                latencies_ms.append(elapsed)
                print(f"FAIL ({elapsed:.0f}ms) — {exc}")
                scored_examples.append(
                    RagEvaluationExampleCreate(
                        id=ex["id"],
                        query=query,
                        tenant_fixture=ex["tenant_fixture"],
                        expected_behavior=ex["expected_behavior"],
                        expected_source_labels=ex.get("expected_source_labels", []),
                        notes=ex.get("notes"),
                        passed=False,
                        summary={"error": str(exc), "latency_ms": elapsed},
                    )
                )
                continue

            elapsed = (time.monotonic() - start) * 1000
            latencies_ms.append(elapsed)

            passed, summary = score_example(
                result,
                ex["expected_behavior"],
                ex.get("expected_source_labels", []),
            )
            summary["latency_ms"] = elapsed

            marker = "PASS" if passed else "FAIL"
            print(f"{marker} ({elapsed:.0f}ms)")

            scored_examples.append(
                RagEvaluationExampleCreate(
                    id=ex["id"],
                    query=query,
                    tenant_fixture=ex["tenant_fixture"],
                    expected_behavior=ex["expected_behavior"],
                    expected_source_labels=ex.get("expected_source_labels", []),
                    notes=ex.get("notes"),
                    passed=passed,
                    summary=summary,
                )
            )

        # ── Aggregate summary ────────────────────────────────────
        passed_count = sum(1 for e in scored_examples if e.passed)
        failed_count = len(scored_examples) - passed_count
        latencies_ms.sort()
        n = len(latencies_ms)

        agg_summary = {
            "total_examples": len(scored_examples),
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": round(passed_count / len(scored_examples), 4) if scored_examples else 0.0,
            "latency_ms": {
                "min": round(latencies_ms[0], 1) if n > 0 else 0,
                "max": round(latencies_ms[-1], 1) if n > 0 else 0,
                "avg": round(sum(latencies_ms) / n, 1) if n > 0 else 0,
                "p50": round(latencies_ms[n // 2], 1) if n > 0 else 0,
                "p95": round(latencies_ms[int(n * 0.95)], 1) if n > 0 else 0,
            },
            "latency_max_ms": args.latency_max_ms,
            "latency_violations": sum(1 for l in latencies_ms if l > args.latency_max_ms),
        }

        # ── Persist ──────────────────────────────────────────────
        run = await service.record_evaluation_run_with_examples(
            run_label=run_label,
            examples=scored_examples,
            summary=agg_summary,
        )

        # ── Report ───────────────────────────────────────────────
        print()
        print(f"Evaluation run: {run_label}")
        print(f"  Total:   {agg_summary['total_examples']}")
        print(f"  Passed:  {agg_summary['passed']}")
        print(f"  Failed:  {agg_summary['failed']}")
        print(f"  Rate:    {agg_summary['pass_rate'] * 100:.1f}%")
        lat = agg_summary["latency_ms"]
        print(f"  Latency: min={lat['min']}ms max={lat['max']}ms avg={lat['avg']}ms "
              f"p50={lat['p50']}ms p95={lat['p95']}ms")
        if agg_summary["latency_violations"]:
            print(f"  ⚠  {agg_summary['latency_violations']} violation(s) > {args.latency_max_ms}ms")
        print(f"  Run ID:  {run.id}")
        print()

        # ── Enforce ──────────────────────────────────────────────
        if agg_summary["latency_violations"]:
            print(f"❌ Latency threshold exceeded: {agg_summary['latency_violations']} violation(s) "
                  f"(max {args.latency_max_ms}ms)")
            sys.exit(1)

        if failed_count:
            print(f"❌ {failed_count} example(s) failed")
            sys.exit(1)

        print("✅ All examples passed. Latency within threshold.")


if __name__ == "__main__":
    asyncio.run(main())
