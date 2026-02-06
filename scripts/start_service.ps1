# ════════════════════════════════════════════════════════════════════════════
# 🌿 ALİM — Start Service Entrypoint
# ════════════════════════════════════════════════════════════════════════════
# Professional, simplified service starter.
# Usage: ./start_service.ps1 -Service "FastAPI"
#        ./start_service.ps1 -Service "FastAPI" -UnifiedLog  # Tee to unified log
# ════════════════════════════════════════════════════════════════════════════

param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("FastAPI", "UI", "LangGraph", "MCP", "Docker")]
    [string]$Service,

    [switch]$Headless = $false,
    [switch]$UnifiedLog = $false  # Tee output to unified log file
)

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Setup unified logging
$logsDir = Join-Path $projectRoot "logs"
$unifiedLogFile = Join-Path $logsDir "alim_unified.log"

if ($UnifiedLog) {
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
    if (-not (Test-Path $unifiedLogFile)) {
        "" | Set-Content $unifiedLogFile
    }
}

# Helper function to write to unified log with service prefix
function Write-UnifiedLog {
    param([string]$Line)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $entry = "[$timestamp] [$Service] $Line"

    # Write to console
    Write-Host $Line

    # Append to unified log if enabled
    if ($UnifiedLog) {
        $entry | Out-File -Append -FilePath $unifiedLogFile -Encoding utf8
    }
}

# 1. Prepare Environment
$env:PYTHONPATH = "$projectRoot\src"
$venv = "$projectRoot\.venv\Scripts"

# Load .env natively
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            # Strip inline comments (everything after #)
            $content = $line -split "#", 2 | Select-Object -First 1
            $parts = $content.Trim() -split '=', 2
            if ($parts.Count -eq 2) {
                $key = $parts[0].Trim()
                $value = $parts[1].Trim()
                [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
            }
        }
    }
}

# 2. Define Commands (each sets ALIM_SERVICE_NAME for unified logging)
$commands = @{
    "FastAPI"   = {
        $env:ALIM_SERVICE_NAME = "API"
        & "$venv\uvicorn.exe" alim.api.main:app --host localhost --port 8000 --reload
    }
    "UI"        = {
        $env:ALIM_SERVICE_NAME = "UI"
        $env:PYTHONPATH = "$projectRoot\src;$projectRoot\demo-ui"
        Set-Location "demo-ui"
        $args = @("run", "app.py", "-w", "--port", "8501")
        if ($Headless) { $args += "--headless" }
        & "$venv\python.exe" -m chainlit $args
    }
    "LangGraph" = {
        $env:ALIM_SERVICE_NAME = "LANGGRAPH"
        # Use langgraph CLI directly (not python -m)
        # Must run from the directory containing langgraph.json for relative paths to work
        Set-Location "deploy/langgraph"
        & "$venv\langgraph.exe" dev --no-browser
    }
    "MCP"       = {
        $env:ALIM_SERVICE_NAME = "MCP"
        & "$venv\python.exe" -m uvicorn alim.mcp_server.main:app --port 7777 --reload
    }
    "Docker"    = {
        $env:ALIM_SERVICE_NAME = "DOCKER"
        # Only include llm-local profile when using Ollama
        $profiles = @("--profile", "core", "--profile", "observability")
        if ($env:ALIM_LLM_PROVIDER -eq "ollama") {
            $profiles += @("--profile", "llm-local")
            Write-Host "  📦 Including Ollama (llm-local profile)" -ForegroundColor DarkCyan
        } else {
            Write-Host "  ☁️ Using cloud LLM ($($env:ALIM_LLM_PROVIDER)) - skipping Ollama" -ForegroundColor DarkCyan
        }
        docker compose @profiles up -d
    }
}

# 3. Execute
Write-Host "🌿 Starting $Service..." -ForegroundColor Cyan
if ($commands.ContainsKey($Service)) {
    & $commands[$Service]
}
else {
    Write-Error "Unknown service: $Service"
    exit 1
}
