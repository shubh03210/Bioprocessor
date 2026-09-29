# Local production-like check (Windows)
# 1) Build SPA into backend/app/static
# 2) Start uvicorn with bootstrap
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "== frontend build =="
Set-Location "$Root\frontend"
npm run build

Write-Host "== copy to backend/app/static =="
$static = "$Root\backend\app\static"
if (Test-Path $static) { Remove-Item -Recurse -Force $static }
New-Item -ItemType Directory -Path $static | Out-Null
Copy-Item -Recurse "$Root\frontend\dist\*" $static

Write-Host "== start (BOOTSTRAP_ON_STARTUP) =="
Set-Location "$Root\backend"
if (Test-Path ".\.venv\Scripts\Activate.ps1") { .\.venv\Scripts\Activate.ps1 }
$env:ENVIRONMENT = "production"
$env:BOOTSTRAP_ON_STARTUP = "true"
$env:SEED_CONTROL_READINGS = "true"
$env:CORS_ORIGINS = "*"
$env:DATA_KIT_PATH = "../data_kit"
Write-Host "Open http://127.0.0.1:8000/  (Schedule + Control via same origin)"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
