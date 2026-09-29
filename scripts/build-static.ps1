# Rebuild Vite SPA into backend/app/static (commit the result for hosting).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location "$Root\frontend"
npm run build

$static = "$Root\backend\app\static"
if (Test-Path $static) { Remove-Item -Recurse -Force $static }
New-Item -ItemType Directory -Path $static | Out-Null
Copy-Item -Recurse "$Root\frontend\dist\*" $static
Write-Host "Wrote $static - commit backend/app/static for deploy."
