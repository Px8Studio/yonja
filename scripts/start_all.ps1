# ════════════════════════════════════════════════════════════════════════════
# 🌿 YONCA AI — Start All (CLI Wrapper)
# ════════════════════════════════════════════════════════════════════════════
# Wrapper around start_service.ps1 to start everything in background.
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n🌿 YONCA AI — Starting Services (CLI Mode)`n" -ForegroundColor Cyan

# 1. Start Docker (blocking, wait for it)
Write-Host "🐳 Starting Docker..." -ForegroundColor Yellow
pwsh -File "$projectRoot\scripts\start_service.ps1" -Service Docker
Write-Host "✅ Docker started" -ForegroundColor Green

# 2. Start Python Services (Hidden Background Windows)
$services = "FastAPI", "LangGraph", "MCP"
foreach ($s in $services) {
    Write-Host "🌿 Starting $s..." -ForegroundColor Yellow
    Start-Process pwsh -ArgumentList "-File", "$projectRoot\scripts\start_service.ps1", "-Service", $s -WindowStyle Hidden
}

# 3. Start UI (Headless, Background)
Write-Host "🖥️ Starting UI..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-File", "$projectRoot\scripts\start_service.ps1", "-Service", "UI", "-Headless" -WindowStyle Hidden

Write-Host "`n✅ All services started in background windows!" -ForegroundColor Green
Write-Host "   Run 'scripts/stop_all.ps1' or check Task Manager to stop." -ForegroundColor DarkGray
