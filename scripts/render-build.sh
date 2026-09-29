#!/usr/bin/env bash
# Host build: Python deps only. SPA is committed under backend/app/static
# (rebuild locally with scripts/build-static.ps1 or npm run build + copy).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
python -m pip install -r requirements.txt
echo "Build OK (static present: $([ -f app/static/index.html ] && echo yes || echo NO))"
