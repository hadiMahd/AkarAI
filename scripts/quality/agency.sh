#!/usr/bin/env bash
set -euo pipefail

cd apps/agency
npm ci
npm run build
npm test
