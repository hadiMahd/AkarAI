#!/usr/bin/env bash
set -euo pipefail

docker compose exec backend python -m pytest tests/unit tests/smoke
