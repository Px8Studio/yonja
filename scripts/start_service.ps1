# ════════════════════════════════════════════════════════════════════════════
# 🌿 YONCA AI — Start Service Helper
# ════════════════════════════════════════════════════════════════════════════
# centralized script to start individual services with correct environment
#
# Usage:
#   ./start_service.ps1 -Service "FastAPI"
#   ./start_service.ps1 -Service "UI" -Headless
# ════════════════════════════════════════════════════════════════════════════

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("FastAPI", "UI", "LangGraph", "MCP", "Docker")]
    [string]$Service,

    [switch]$Headless = $false
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = "$projectRoot\.env"

# 1. Load .env file
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match '^\s*[^#]' -and $_ -match '=' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        $key = $key.Trim()
        $value = $value.Trim()

        # Remove quotes if present
        if ($value -match '^"(.*)"$') { $value = $matches[1] }
        elseif ($value -match "^'(.*)'$") { $value = $matches[1] }

        # Set environment variable
        [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)

        # COMPATIBILITY HACK:
        # If variable starts with YONCA_, also set the non-prefixed version
        # so legacy code (demo-ui) works without changes.
        if ($key -like "YONCA_*") {
            $legacyKey = $key -replace "^YONCA_", ""
            [System.Environment]::SetEnvironmentVariable($legacyKey, $value, [System.EnvironmentVariableTarget]::Process)
        }
    }
} else {
    Write-Warning "⚠️  .env file not found at $envFile. Using defaults."
}

# 2. Set Dynamic Environment Variables
$venvScripts = "$projectRoot\.venv\Scripts"
$env:PYTHONPATH = "$projectRoot\src"
if ($Service -eq "UI") {
    $env:PYTHONPATH = "$projectRoot\src;$projectRoot\demo-ui"
}

# 3. Define Commands
$commands = @{
    "FastAPI"   = {
        & "$venvScripts\python.exe" -m uvicorn yonca.api.main:app --host localhost --port 8000 --reload --log-level info
    }
    "UI"        = {
        if ($Headless) {
            & "$venvScripts\chainlit.exe" run app.py -w --port 8501 --headless
        } else {
            & "$venvScripts\chainlit.exe" run app.py -w --port 8501
        }
    }
    "LangGraph" = {
        & "$venvScripts\langgraph.exe" dev --no-browser
    }
    "MCP"       = {
        & "$venvScripts\python.exe" -m uvicorn yonca.mcp_server.main:app --port 7777 --reload
    }
    "Docker"    = {
        docker-compose -f "$projectRoot\docker-compose.local.yml" up -d postgres ollama redis langfuse-db langfuse-server
    }
}

# 4. Execute
Write-Host "🌿 Starting $Service..." -ForegroundColor Cyan
if ($commands.ContainsKey($Service)) {
    # Change specific working directories if needed
    if ($Service -eq "UI") { Set-Location "$projectRoot\demo-ui" }
    else { Set-Location $projectRoot }

    try {
        & $commands[$Service]
    } catch {
        Write-Error "Failed to start $Service : $_"
        exit 1
    }
} else {
    Write-Error "Unknown service: $Service"
    exit 1
}
