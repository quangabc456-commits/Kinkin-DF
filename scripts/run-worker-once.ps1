# Chạy cron_worker 1 lần thủ công ngoài PM2 (debug / dev).
#
# Usage:
#   .\scripts\run-worker-once.ps1                # dry-run, batch nhỏ
#   .\scripts\run-worker-once.ps1 -DryRun:$false # call API thật
#   .\scripts\run-worker-once.ps1 -Batch 5

param(
    [bool]$DryRun = $true,
    [int]$Batch = 5,
    [int]$DaysBack = 30,
    [switch]$SkipRefresh,
    [switch]$SkipPrefetch,
    [switch]$SkipCreatePgh,
    [switch]$SkipKinkin
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "Không tìm thấy .venv. Chạy: python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt"
}

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"

$cmdArgs = @("-m", "app.workers.cron_worker", "--batch", $Batch, "--days-back", $DaysBack)
if ($DryRun) { $cmdArgs += "--dry-run" }
if ($SkipRefresh)   { $cmdArgs += "--skip-refresh" }
if ($SkipPrefetch)  { $cmdArgs += "--skip-prefetch" }
if ($SkipCreatePgh) { $cmdArgs += "--skip-create-pgh" }
if ($SkipKinkin)    { $cmdArgs += "--skip-kinkin" }

Write-Host "Running: python $($cmdArgs -join ' ')" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" @cmdArgs
