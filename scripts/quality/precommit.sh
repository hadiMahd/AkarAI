#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${PRECOMMIT_BASE_REF:-main}"

if git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  FROM_REF="$(git merge-base HEAD "$BASE_REF")"
  pre-commit run --from-ref "$FROM_REF" --to-ref HEAD
else
  pre-commit run --all-files
fi
