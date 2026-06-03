# Restart PM2 worker của project Kinkin-DF.
#
# Bước:
#   1. Xóa worker cũ tên "kinkin-cron-worker" nếu còn (sau migrate tên)
#   2. Start lại worker với tên mới "kkdf-cron" từ ecosystem.config.js
#   3. Save danh sách PM2 để auto-start sau reboot
#   4. Verify status + log 1 vòng
#
# Usage:
#   .\scripts\restart-kkdf-cron.ps1
#   .\scripts\restart-kkdf-cron.ps1 -RunOnce          # chạy 1 vòng manual trước, kèm verify
#   .\scripts\restart-kkdf-cron.ps1 -RunOnce -DryRun  # 1 vòng dry-run

param(
    [switch]$RunOnce,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Error "PM2 chưa cài. Chạy: npm i -g pm2"
}

Write-Host "=== Bước 1: xóa worker cũ (nếu còn) ===" -ForegroundColor Cyan
pm2 delete kinkin-cron-worker 2>&1 | Out-String | Write-Host
pm2 delete kkdf-cron 2>&1 | Out-String | Write-Host

if ($RunOnce) {
    Write-Host "=== Bước 2a: chạy worker 1 vòng manual để verify ===" -ForegroundColor Cyan
    $cronArgs = @("-m", "app.workers.cron_worker", "--batch", 10)
    if ($DryRun) { $cronArgs += "--dry-run" }
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUNBUFFERED = "1"
    & ".\.venv\Scripts\python.exe" @cronArgs
    Write-Host ""
    Write-Host "Nếu output ở trên OK, tiếp tục PM2 setup..." -ForegroundColor Yellow
    Read-Host "Press Enter để tiếp tục, Ctrl+C để dừng"
}

Write-Host "=== Bước 2: start worker mới `"kkdf-cron`" từ ecosystem ===" -ForegroundColor Cyan
pm2 start ecosystem.config.js 2>&1 | Out-String | Write-Host

Write-Host "=== Bước 3: save PM2 cho auto-start ===" -ForegroundColor Cyan
pm2 save 2>&1 | Out-String | Write-Host

Write-Host "=== Bước 4: status hiện tại ===" -ForegroundColor Cyan
pm2 list 2>&1 | Select-String -Pattern "name|kkdf|kinkin"

Write-Host ""
Write-Host "Done. Theo dõi log: pm2 logs kkdf-cron --lines 30" -ForegroundColor Green
