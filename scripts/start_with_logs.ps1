# ════════════════════════════════════════════════════════════════════════════
# 🌿 YONCA AI — Start with Logs (Agent Observable)
# ════════════════════════════════════════════════════════════════════════════
# Wrapper around start_service.ps1 to start everything with log redirection.
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
$projectRoot = Split-Path -Parent $PSScriptRoot
$logDir = "$projectRoot\logs"

# Ensure logs directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

Write-Host "`n🌿 YONCA AI — Starting Services (Observable Mode)`n" -ForegroundColor Cyan
Write-Host "📂 Logs will be written to: $logDir" -ForegroundColor DarkGray

# 1. Start Docker (blocking)
Write-Host "🐳 Starting Docker..." -ForegroundColor Yellow
# Docker keeps its own logs usually, but we can redirect the startup output
pwsh -File "$projectRoot\scripts\start_service.ps1" -Service Docker *>> "$logDir\docker.log"
Write-Host "✅ Docker started" -ForegroundColor Green

# 2. Start Services with Logs
function Start-ServiceWithLog {
    param($Name, $ServiceKey, $LogFile, $Headless=$false)
    Write-Host "$Name..." -ForegroundColor Yellow

    $argsList = @("-File", "$projectRoot\scripts\start_service.ps1", "-Service", $ServiceKey)
    if ($Headless) { $argsList += "-Headless" }

    $p = Start-Process -FilePath "pwsh" -ArgumentList $argsList -WorkingDirectory $projectRoot `
        -RedirectStandardOutput "$logDir\$LogFile.log" `
        -RedirectStandardError "$logDir\$LogFile.err.log" `
        -WindowStyle Hidden `
        -PassThru

    Write-Host "   → PID: $($p.Id) | Log: $LogFile.log" -ForegroundColor DarkGray
}

Start-ServiceWithLog -Name "🌿 FastAPI"       -ServiceKey "FastAPI"   -LogFile "api"
Start-ServiceWithLog -Name "🎨 LangGraph"     -ServiceKey "LangGraph" -LogFile "langgraph"
Start-ServiceWithLog -Name "🧠 ZekaLab MCP"   -ServiceKey "MCP"       -LogFile "mcp"
Start-ServiceWithLog -Name "🖥️ Chainlit UI"   -ServiceKey "UI"        -LogFile "ui" -Headless $true

Write-Host "`n✅ All services started in background!" -ForegroundColor Green
Write-Host "Use 'Get-Content logs\*.log -Tail 10' to inspect." -ForegroundColor Cyan
