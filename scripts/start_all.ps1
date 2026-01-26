# 🌿 ALİM — Start All (Simplified)
# Starts all services in foreground/background windows.

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n🌿 ALİM — Starting All Services`n" -ForegroundColor Cyan

# 1. Start Docker
pwsh -File "$projectRoot\scripts\start_service.ps1" -Service Docker

# 2. Start Others in Background Windows
$services = "FastAPI", "LangGraph", "MCP", "UI"
foreach ($s in $services) {
    Write-Host "🚀 Starting $s..." -ForegroundColor Green
    Start-Process "pwsh" -ArgumentList "-File", "$projectRoot\scripts\start_service.ps1", "-Service", $s -NoNewWindow:$false
}

Write-Host "`n✅ Done." -ForegroundColor Green
