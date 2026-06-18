#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ "${USE_RAGAS_EVALS:-0}" != "1" ]]; then
  echo "Skipping live RAG evals. Set USE_RAGAS_EVALS=1 to enable."
  exit 0
fi

cd backend
ARGS=(--mode "${RAG_EVAL_MODE:-blocking}")

if [[ -n "${RAG_EVAL_DATASET:-}" ]]; then
  ARGS+=(--dataset "${RAG_EVAL_DATASET}")
fi

if [[ -n "${RAG_EVAL_MANIFEST:-}" ]]; then
  ARGS+=(--manifest "${RAG_EVAL_MANIFEST}")
fi

if [[ -n "${RAG_EVAL_TOP_K:-}" ]]; then
  ARGS+=(--top-k "${RAG_EVAL_TOP_K}")
fi

if [[ "${RAG_EVAL_ALLOW_JUDGE_FAILURES:-0}" == "1" ]]; then
  ARGS+=(--allow-judge-failures)
fi

"${PYTHON_BIN}" ../scripts/ci/run_rag_eval.py "${ARGS[@]}"
