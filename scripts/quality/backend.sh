#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

cd backend
"${PYTHON_BIN}" -m pytest tests/unit
