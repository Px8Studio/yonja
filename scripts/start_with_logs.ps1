# ════════════════════════════════════════════════════════════════════════════
# 🌿 YONCA AI — Start with Logs (Agent Observable)
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

# 1. Docker
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose -f "$projectRoot\docker-compose.local.yml" up -d postgres ollama redis langfuse-db langfuse-server
Write-Host "✅ Docker services started" -ForegroundColor Green

# 2. Clear cache
Get-ChildItem -Path $projectRoot -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "🧹 Cache cleared" -ForegroundColor Green

# 3. Start Python services with log redirection
$venvPath = "$projectRoot\.venv\Scripts"
$env:PYTHONPATH = "$projectRoot\src"
$env:DATABASE_URL = "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"
$env:ZEKALAB_MCP_ENABLED = "true"
$env:ZEKALAB_MCP_URL = "http://localhost:7777"
$env:PYTHONIOENCODING = "utf-8"

# Helper to start process with logs
function Start-ServiceWithLog {
    param($Name, $FilePath, $Arguments, $WorkDir, $LogFile)
    Write-Host "$Name..." -ForegroundColor Yellow

    # Split string arguments into array for Start-Process
    $ArgsArray = $Arguments -split " "

    $p = Start-Process -FilePath $FilePath -ArgumentList $ArgsArray -WorkingDirectory $WorkDir `
        -RedirectStandardOutput "$logDir\$LogFile.log" `
        -RedirectStandardError "$logDir\$LogFile.err.log" `
        -WindowStyle Hidden `
        -PassThru

    Write-Host "   → PID: $($p.Id) | Log: $LogFile.log" -ForegroundColor DarkGray
}

# LangGraph
$env:PYTHONPATH = "$projectRoot\src"
Start-ServiceWithLog -Name "🎨 LangGraph" -FilePath "$venvPath\langgraph.exe" -Arguments "dev" -WorkDir $projectRoot -LogFile "langgraph"

# FastAPI
Start-ServiceWithLog -Name "🌿 FastAPI" -FilePath "$venvPath\python.exe" -Arguments "-m uvicorn yonca.api.main:app --host localhost --port 8000 --reload" -WorkDir $projectRoot -LogFile "api"

# MCP
Start-ServiceWithLog -Name "🧠 ZekaLab MCP" -FilePath "$venvPath\python.exe" -Arguments "-m uvicorn yonca.mcp_server.main:app --port 7777 --reload" -WorkDir $projectRoot -LogFile "mcp"

# Chainlit
$env:PYTHONPATH = "$projectRoot\src;$projectRoot\demo-ui"
$env:INTEGRATION_MODE = "direct"
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:ENABLE_DATA_PERSISTENCE = "true"
Start-ServiceWithLog -Name "🖥️ Chainlit UI" -FilePath "$venvPath\chainlit.exe" -Arguments "run app.py -w --port 8501 --headless" -WorkDir "$projectRoot\demo-ui" -LogFile "ui"

Write-Host "`n✅ All services started in background!" -ForegroundColor Green
Write-Host "Use 'Get-Content logs\*.log -Tail 10' to inspect." -ForegroundColor Cyan
