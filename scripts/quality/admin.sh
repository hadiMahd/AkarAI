#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

cd admin
"${PYTHON_BIN}" -m pytest tests
