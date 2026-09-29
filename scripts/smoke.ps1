# Local smoke: backend tests + simulator tests + frontend build
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "== backend import =="
Set-Location "$Root\backend"
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  .\.venv\Scripts\Activate.ps1
}
python -c "from app.main import app; print('backend import OK', app.title)"

Write-Host "== backend pytest =="
python -m pytest

Write-Host "== simulator pytest =="
Set-Location "$Root\simulator"
$env:PYTHONPATH = "."
python -m pytest

Write-Host "== simulator hello =="
python -m bbp_simulator --hello

Write-Host "== frontend build =="
Set-Location "$Root\frontend"
if (Test-Path "node_modules") {
  npm run build
} else {
  Write-Host "skip frontend build (run npm install first)"
}

Write-Host "Smoke OK (Phase 12)"
