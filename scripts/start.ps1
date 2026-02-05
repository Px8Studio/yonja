# ════════════════════════════════════════════════════════════════════════════
# 🌿 ALİM — Simplified Startup
# ════════════════════════════════════════════════════════════════════════════
# Starts Infrastructure (Docker) and Application Services.
# ════════════════════════════════════════════════════════════════════════════

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "`n🌿 ALİM — Starting Services`n" -ForegroundColor Cyan

# 1. Start Infrastructure
Write-Host "🐳 Starting Infrastructure (Docker)..." -ForegroundColor Yellow
docker-compose -f "docker-compose.local.yml" up -d postgres ollama redis langfuse-db langfuse-server
if ($LASTEXITCODE -ne 0) {
    Write-Warning "⚠️  Docker failed to start. Ensure Docker Desktop is running."
}

# 2. Set Environment
$env:PYTHONPATH = "$projectRoot\src"
$venv = "$projectRoot\.venv\Scripts"

# Load .env natively
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match '^\s*[^#]' -and $_ -match '=' } | ForEach-Object {
        $parts = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), [System.EnvironmentVariableTarget]::Process)
    }
}

# 3. Start Services
$services = @{
    "FastAPI"   = "uvicorn alim.api.main:app --host localhost --port 8000 --reload"
    "LangGraph" = "langgraph dev --no-browser"
    "MCP"       = "python -m uvicorn alim.mcp_server.main:app --port 7777 --reload"
    "UI"        = "chainlit run app.py -w --port 8501"
}

# 3. Start Services (Background, No Windows)
$logDir = "$projectRoot\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

foreach ($name in $services.Keys) {
    Write-Host "🚀 Starting $name (Background)..." -ForegroundColor Green
    $logFile = "$logDir\$($name.ToLower()).log"
    $errFile = "$logDir\$($name.ToLower()).err.log"

    if ($name -eq "UI") {
        $env:PYTHONPATH = "$projectRoot\src;$projectRoot\demo-ui"
        Start-Process "pwsh" -ArgumentList "-Command", "Set-Location demo-ui; & '$venv\chainlit.exe' run app.py -w --port 8501" -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile
    }
    elseif ($name -eq "FastAPI") {
        $env:PYTHONPATH = "$projectRoot\src"
        Start-Process "pwsh" -ArgumentList "-Command", "& '$venv\uvicorn.exe' alim.api.main:app --host localhost --port 8000 --reload" -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile
    }
    elseif ($name -eq "LangGraph") {
        $env:PYTHONPATH = "$projectRoot\src"
        Start-Process "pwsh" -ArgumentList "-Command", "& '$venv\langgraph.exe' dev --no-browser" -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile
    }
    elseif ($name -eq "MCP") {
        $env:PYTHONPATH = "$projectRoot\src"
        Start-Process "pwsh" -ArgumentList "-Command", "& '$venv\python.exe' -m uvicorn alim.mcp_server.main:app --port 7777 --reload" -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile
    }
}

Write-Host "`n✅ All services running in background!" -ForegroundColor Green
Write-Host "📂 Logs: $logDir" -ForegroundColor DarkGray
Write-Host "💡 Use 'Get-Content logs\$($services.Keys[0].ToLower()).log -Tail 20 -Wait' to follow a log." -ForegroundColor Cyan
