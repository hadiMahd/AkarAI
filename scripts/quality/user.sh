#!/usr/bin/env bash
set -euo pipefail

cd apps/user
npm ci
npm run build
npm test
