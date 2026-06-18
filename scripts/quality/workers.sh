#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

cd workers
"${PYTHON_BIN}" -m pytest tests
