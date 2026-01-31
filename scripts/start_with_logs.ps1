# 🌿 ALİM — Start with Logs (Simplified)
# Starts all services and redirects output to logs/

$projectRoot = Split-Path -Parent $PSScriptRoot
$logDir = "$projectRoot\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

Write-Host "`n🌿 ALİM — Starting Services (Observable Mode)`n" -ForegroundColor Cyan

# 1. Start Docker
Write-Host "🐳 Starting Docker..." -ForegroundColor Yellow
pwsh -File "$projectRoot\scripts\start_service.ps1" -Service Docker

# 2. Start Services in Background
$services = "FastAPI", "LangGraph", "MCP", "UI"
foreach ($s in $services) {
    Write-Host "🚀 Starting $s..." -ForegroundColor Green
    $logFile = "$logDir\$($s.ToLower()).log"
    $errFile = "$logDir\$($s.ToLower()).err.log"

    $args = @("-File", "$projectRoot\scripts\start_service.ps1", "-Service", $s)
    if ($s -eq "UI") { $args += "-Headless" }

    Start-Process "pwsh" -ArgumentList $args -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile
}

Write-Host "`n✅ All services started in background!" -ForegroundColor Green
Write-Host "📂 Logs: $logDir" -ForegroundColor DarkGray
