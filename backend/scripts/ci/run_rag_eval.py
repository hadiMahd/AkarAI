#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.common.config import configure_secrets
from app.common.database import async_session_factory
from app.rag.evals import (
    BLOCKING_MODE,
    DEFAULT_DATASET_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_TOP_K,
    MANUAL_MODE,
    run_eval,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run live RAGAS evaluation for agency RAG")
    parser.add_argument(
        "--mode",
        choices=[BLOCKING_MODE, MANUAL_MODE],
        default=BLOCKING_MODE,
        help="Use the blocking 20-example suite or the fuller manual suite.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to the JSONL evaluation dataset.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to the fixture manifest used for self-seeding.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Number of chunks to retrieve per query.",
    )
    parser.add_argument(
        "--run-label",
        type=str,
        default=None,
        help="Optional label for the evaluation run.",
    )
    parser.add_argument(
        "--allow-judge-failures",
        action="store_true",
        help="Do not fail the run when Azure judge calls fail. Intended for manual mode only.",
    )
    return parser


def _print_summary(summary: dict, run_id: str) -> None:
    metrics = summary["metrics"]
    latency = summary["latency_ms"]
    print()
    print(f"Evaluation run: {summary['run_label']}")
    print(f"  Mode:    {summary['mode']}")
    print(f"  Total:   {summary['total_examples']}")
    print(f"  Answer:  {summary['answerable_examples']}")
    print(f"  Refuse:  {summary['refusal_examples']}")
    print(f"  Faith:   {metrics.get('faithfulness')}")
    print(f"  Ctx P:   {metrics.get('context_precision')}")
    print(f"  Ctx R:   {metrics.get('context_recall')}")
    print(f"  Ans Rel: {metrics.get('answer_relevancy')}")
    print(f"  Hit@1:   {metrics.get('hit_at_1')}")
    print(f"  Hit@5:   {metrics.get('hit_at_5')}")
    print(f"  Leak:    {metrics.get('tenant_leakage_count')}")
    print(
        f"  Latency: min={latency['min']}ms max={latency['max']}ms avg={latency['avg']}ms "
        f"p50={latency['p50']}ms p95={latency['p95']}ms"
    )
    print(f"  Judge failures: {summary['judge_failures']}")
    print(f"  Run ID:  {run_id}")
    if summary["threshold_failures"]:
        print(f"  Threshold failures: {', '.join(summary['threshold_failures'])}")
    print()


async def _main() -> int:
    configure_secrets()
    args = _build_parser().parse_args()
    run_label = (
        args.run_label
        or f"ragas-{args.mode}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )

    result = await run_eval(
        async_session_factory,
        dataset_path=args.dataset,
        manifest_path=args.manifest,
        mode=args.mode,
        top_k=args.top_k,
        run_label=run_label,
        allow_judge_failures=args.allow_judge_failures,
    )

    summary = result["summary"]
    run = result["run"]
    _print_summary(summary, str(run.id))

    if summary["threshold_failures"]:
        print("RAGAS evaluation failed thresholds.", file=sys.stderr)
        return 1

    print("RAGAS evaluation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
