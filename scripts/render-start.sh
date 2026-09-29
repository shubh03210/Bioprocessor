#!/usr/bin/env bash
# Start API (+ SPA if built into app/static). Used by Render / generic PaaS.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

export ENVIRONMENT="${ENVIRONMENT:-production}"
export BOOTSTRAP_ON_STARTUP="${BOOTSTRAP_ON_STARTUP:-true}"
export SEED_CONTROL_READINGS="${SEED_CONTROL_READINGS:-true}"
export DATA_KIT_PATH="${DATA_KIT_PATH:-../data_kit}"
export CORS_ORIGINS="${CORS_ORIGINS:-*}"

PORT="${PORT:-8000}"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
