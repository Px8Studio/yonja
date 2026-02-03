# ════════════════════════════════════════════════════════════════════════════
# 🌿 ALİM — Start Service Entrypoint
# ════════════════════════════════════════════════════════════════════════════
# Professional, simplified service starter.
# Usage: ./start_service.ps1 -Service "FastAPI"
# ════════════════════════════════════════════════════════════════════════════

param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("FastAPI", "UI", "LangGraph", "MCP", "Docker")]
    [string]$Service,

    [switch]$Headless = $false
)

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

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

# 2. Define Commands
$commands = @{
    "FastAPI"   = { & "$venv\uvicorn.exe" alim.api.main:app --host localhost --port 8000 --reload }
    "UI"        = {
        $env:PYTHONPATH = "$projectRoot\src;$projectRoot\demo-ui"
        Set-Location "demo-ui"
        $args = @("run", "app.py", "-w", "--port", "8501")
        if ($Headless) { $args += "--headless" }
        & "$venv\python.exe" -m chainlit $args
    }
    "LangGraph" = {
        # Use langgraph CLI directly (not python -m)
        # Must run from the directory containing langgraph.json for relative paths to work
        Set-Location "deploy/langgraph"
        & "$venv\langgraph.exe" dev --no-browser
    }
    "MCP"       = { & "$venv\python.exe" -m uvicorn alim.mcp_server.main:app --port 7777 --reload }
    "Docker"    = { docker compose --profile core --profile observability up -d }
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
