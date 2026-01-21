# ════════════════════════════════════════════════════════════════════════════
# 🌿 YONCA AI — Start All (CLI fallback)
# ════════════════════════════════════════════════════════════════════════════
#
# NOTE: Prefer using VS Code tasks (Ctrl+Shift+P → "Run Task" → "🚀 Start All")
#       for better experience with live logs in separate terminal panels.
#
# This script is a CLI fallback for headless/CI scenarios.
#
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n🌿 YONCA AI — Starting Services`n" -ForegroundColor Cyan

# 1. Docker
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose -f "$projectRoot\docker-compose.local.yml" up -d postgres ollama redis langfuse-db langfuse-server
Write-Host "✅ Docker services started" -ForegroundColor Green

# 2. Clear cache
Get-ChildItem -Path $projectRoot -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "🧹 Cache cleared" -ForegroundColor Green

# 3. Start Python services (hidden windows for CLI mode)
$venvPath = "$projectRoot\.venv\Scripts"
$env:PYTHONPATH = "$projectRoot\src"
$env:DATABASE_URL = "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"

Write-Host "🎨 Starting LangGraph..." -ForegroundColor Yellow
Start-Process -FilePath "$venvPath\langgraph.exe" -ArgumentList "dev" -WorkingDirectory $projectRoot -WindowStyle Hidden

Write-Host "🌿 Starting FastAPI..." -ForegroundColor Yellow
Start-Process -FilePath "$venvPath\python.exe" -ArgumentList "-m uvicorn yonca.api.main:app --host localhost --port 8000 --reload" -WorkingDirectory $projectRoot -WindowStyle Hidden

Write-Host "🖥️ Starting Chainlit..." -ForegroundColor Yellow
$env:PYTHONPATH = "$projectRoot\src;$projectRoot\demo-ui"
$env:INTEGRATION_MODE = "direct"
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:ENABLE_DATA_PERSISTENCE = "true"
Start-Process -FilePath "$venvPath\chainlit.exe" -ArgumentList "run app.py -w --port 8501 --headless" -WorkingDirectory "$projectRoot\demo-ui" -WindowStyle Hidden

Write-Host "`n✅ All services started!`n" -ForegroundColor Green
Write-Host "📡 Endpoints:" -ForegroundColor White
Write-Host "   🌿 API:      http://localhost:8000"
Write-Host "   📘 Swagger:  http://localhost:8000/docs"
Write-Host "   🎨 LangGraph: http://localhost:2024"
Write-Host "   📊 Langfuse: http://localhost:3001"
Write-Host "   💬 Chat UI:  http://localhost:8501"
Write-Host ""
