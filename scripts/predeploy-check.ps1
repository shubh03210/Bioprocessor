# Pre-deploy end-to-end API + SPA checks (backend must be on :8000)
$ErrorActionPreference = "Stop"
$Base = "http://127.0.0.1:8000"
$fail = 0

function Ok($msg) { Write-Host "PASS  $msg" -ForegroundColor Green }
function Bad($msg) { Write-Host "FAIL  $msg" -ForegroundColor Red; $script:fail++ }

Write-Host "== health =="
try {
  $h = Invoke-RestMethod "$Base/api/health"
  if ($h.status -eq "ok") { Ok "health $($h.environment)" } else { Bad "health status=$($h.status)" }
} catch { Bad "health unreachable: $_" }

Write-Host "== SPA =="
try {
  $html = Invoke-WebRequest "$Base/" -UseBasicParsing
  if ($html.StatusCode -eq 200 -and $html.Content -match "root") { Ok "SPA /" } else { Bad "SPA /" }
  $ctrl = Invoke-WebRequest "$Base/control" -UseBasicParsing
  if ($ctrl.StatusCode -eq 200) { Ok "SPA /control" } else { Bad "SPA /control" }
} catch { Bad "SPA: $_" }

Write-Host "== schedule =="
try {
  $s = Invoke-RestMethod "$Base/api/schedule?start_date=2025-10-01&end_date=2025-11-15"
  if ($s.unit_operations.Count -ge 6 -and $s.violations.Count -ge 2) {
    Ok "schedule ops=$($s.unit_operations.Count) violations=$($s.violations.Count)"
  } else {
    Bad "schedule ops=$($s.unit_operations.Count) violations=$($s.violations.Count)"
  }
} catch { Bad "schedule: $_" }

Write-Host "== control state =="
try {
  $c = Invoke-RestMethod "$Base/api/control/state?limit=50"
  if ($c.reading_count -ge 60 -and $null -ne $c.current_process_time_h) {
    Ok "control readings=$($c.reading_count) t=$($c.current_process_time_h)"
  } else {
    Bad "control readings=$($c.reading_count) t=$($c.current_process_time_h)"
  }
} catch { Bad "control: $_" }

Write-Host "== forecast =="
try {
  $f = Invoke-RestMethod -Method Post -Uri "$Base/api/forecast"
  if ($f.points.Count -eq 10 -and $f.model_version) {
    Ok "forecast $($f.model_version) points=$($f.points.Count)"
  } else { Bad "forecast shape" }
} catch { Bad "forecast: $_" }

Write-Host "== command accept =="
try {
  # Clear pending if any
  $pending = @(Invoke-RestMethod "$Base/api/control/commands/pending")
  foreach ($p in $pending) {
    if ($p.id) { Invoke-RestMethod -Method Post -Uri "$Base/api/control/commands/$($p.id)/ack" | Out-Null }
  }
  $c = Invoke-RestMethod "$Base/api/control/state?limit=1"
  $t = [double]$c.current_process_time_h
  $cmd = Invoke-RestMethod -Method Post -Uri "$Base/command" -ContentType "application/json" -Body (@{
    setpoint_name = "feed_rate"; value = 8.0; unit = "mL/h"
    apply_at_time_h = $t + (5.0/60.0); source = "manual"
  } | ConvertTo-Json)
  if ($cmd.status -eq "pending") { Ok "command accepted id=$($cmd.id)" } else { Bad "command status=$($cmd.status)" }
  Invoke-RestMethod -Method Post -Uri "$Base/api/control/commands/$($cmd.id)/ack" | Out-Null
} catch { Bad "command accept: $_" }

Write-Host "== command reject bounds =="
try {
  $c = Invoke-RestMethod "$Base/api/control/state?limit=1"
  $t = [double]$c.current_process_time_h
  try {
    Invoke-RestMethod -Method Post -Uri "$Base/command" -ContentType "application/json" -Body (@{
      setpoint_name = "feed_rate"; value = 35.0; unit = "mL/h"
      apply_at_time_h = $t + (5.0/60.0); source = "manual"
    } | ConvertTo-Json) | Out-Null
    Bad "expected 400 for value 35"
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -eq 400) { Ok "command reject out-of-bounds (400)" } else { Bad "reject status=$code" }
  }
} catch { Bad "command reject: $_" }

Write-Host "== controller step =="
try {
  $pending = @(Invoke-RestMethod "$Base/api/control/commands/pending")
  foreach ($p in $pending) {
    if ($p.id) { Invoke-RestMethod -Method Post -Uri "$Base/api/control/commands/$($p.id)/ack" | Out-Null }
  }
  $step = Invoke-RestMethod -Method Post -Uri "$Base/api/control/step"
  if ($step.acted -eq $true -or ($step.acted -eq $false -and $step.reason)) {
    Ok "controller acted=$($step.acted) $($step.reason)"
  } else { Bad "controller step empty" }
  if ($step.command -and $step.command.id) {
    Invoke-RestMethod -Method Post -Uri "$Base/api/control/commands/$($step.command.id)/ack" | Out-Null
  }
} catch { Bad "controller: $_" }

Write-Host ""
if ($fail -eq 0) {
  Write-Host "E2E PRE-DEPLOY: ALL CHECKS PASSED" -ForegroundColor Green
  exit 0
} else {
  Write-Host "E2E PRE-DEPLOY: $fail FAILED" -ForegroundColor Red
  exit 1
}
