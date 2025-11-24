<#
Start backend FastAPI server with correct PYTHONPATH so `app` package is importable.

Usage:
  # start without reload
  .\scripts\start-backend.ps1

  # start with auto-reload (development)
  .\scripts\start-backend.ps1 -Reload
#>

param(
    [switch]$Reload
)

Write-Host "Setting PYTHONPATH=backend" -ForegroundColor Cyan
$env:PYTHONPATH = "backend"

$cmd = "uvicorn app.main:app --host 0.0.0.0 --port 8000"
if ($Reload) { $cmd += " --reload" }

Write-Host "Running: $cmd" -ForegroundColor Green
iex $cmd
