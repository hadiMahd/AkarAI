#!/usr/bin/env bash
set -euo pipefail

./scripts/quality/backend.sh
./scripts/quality/user.sh
./scripts/quality/agency.sh
./scripts/quality/admin.sh
./scripts/quality/workers.sh
./scripts/quality/model_service.sh
