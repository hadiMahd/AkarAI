#!/usr/bin/env bash
set -euo pipefail

docker compose exec lead-model-service python -m pytest tests
