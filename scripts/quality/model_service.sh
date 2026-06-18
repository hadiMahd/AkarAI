#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

cd model-service
"${PYTHON_BIN}" -m pytest tests
