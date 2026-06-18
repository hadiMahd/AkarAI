#!/usr/bin/env bash
set -euo pipefail

docker compose exec worker python -m pytest tests
