# End-to-end API checks for demo readiness (backend must be running)
$ErrorActionPreference = "Stop"
$Base = "http://127.0.0.1:8000"

Write-Host "== health =="
Invoke-RestMethod "$Base/api/health" | ConvertTo-Json -Compress

Write-Host "== schedule (violations expected) =="
$sched = Invoke-RestMethod "$Base/api/schedule?start_date=2025-10-01&end_date=2025-11-15"
Write-Host ("unit_ops={0} violations={1}" -f $sched.unit_operations.Count, $sched.violations.Count)
if ($sched.violations.Count -lt 2) {
  throw "Expected ≥2 seeded violations"
}

Write-Host "== control state =="
$state = Invoke-RestMethod "$Base/api/control/state?limit=50"
Write-Host ("process_time_h={0} readings={1}" -f $state.current_process_time_h, $state.reading_count)

Write-Host "== controller step =="
$step = Invoke-RestMethod -Method Post -Uri "$Base/api/control/step"
$step | ConvertTo-Json -Depth 4 -Compress

Write-Host "== pending commands =="
Invoke-RestMethod "$Base/api/control/commands/pending" | ConvertTo-Json -Depth 4 -Compress

Write-Host "E2E API checks OK"
