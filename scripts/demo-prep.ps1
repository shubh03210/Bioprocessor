# Phase 11 demo prep — bootstrap DB + seed control readings
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "== bootstrap schedule DB =="
Set-Location "$Root\backend"
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  .\.venv\Scripts\Activate.ps1
}
python -m app.db.bootstrap

$health = Invoke-RestMethod "http://127.0.0.1:8000/api/health" -ErrorAction SilentlyContinue
if (-not $health) {
  Write-Host "Backend not reachable at :8000. Start uvicorn first, then re-run this script." -ForegroundColor Yellow
  exit 1
}

Write-Host "== simulator: 70 ticks → /ingest (forecast history) =="
Set-Location "$Root\simulator"
$env:PYTHONPATH = "."
python -m bbp_simulator --run-file "$Root\data_kit\run_A.csv" --max-ticks 70 --no-sleep --post-ingest

Write-Host "== control state snapshot =="
$state = Invoke-RestMethod "http://127.0.0.1:8000/api/control/state?limit=20"
Write-Host ("process_time_h={0} reading_count={1}" -f $state.current_process_time_h, $state.reading_count)

Write-Host ""
Write-Host "Prep OK. Open:"
Write-Host "  Schedule: http://127.0.0.1:5173/"
Write-Host "  Control:  http://127.0.0.1:5173/control"
Write-Host "Follow docs/DEMO_SCRIPT.md for the ≤3 min recording."
