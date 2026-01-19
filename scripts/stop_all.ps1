# scripts/stop_all.ps1
# Yonca AI - Stop All Services
# Gracefully stops all Yonca AI services with visual feedback

$ErrorActionPreference = 'SilentlyContinue'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()

# Colors & Formatting

function Write-Banner {
    Write-Host ''
    Write-Host '  +-----------------------------------------------------------+' -ForegroundColor Magenta
    Write-Host '  |  YONCA AI - Stopping Services                             |' -ForegroundColor Magenta
    Write-Host '  +-----------------------------------------------------------+' -ForegroundColor Magenta
    Write-Host ''
}

function Write-SectionHeader {
    param([string]$Title)
    Write-Host ''
    Write-Host "  -----------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  $Title" -ForegroundColor White
    Write-Host "  -----------------------------------------------------------" -ForegroundColor DarkGray
}

function Write-StatusLine {
    param(
        [string]$Component,
        [string]$Status,
        [string]$Style = "info",
        [string]$Detail = ""
    )
    
    # Style definitions
    switch ($Style) {
        "success" { $symbol = "[OK]"; $color = "Green" }
        "warning" { $symbol = "[!!]"; $color = "Yellow" }
        "error"   { $symbol = "[XX]"; $color = "Red" }
        "info"    { $symbol = "[..]"; $color = "Cyan" }
        "skip"    { $symbol = "[--]"; $color = "DarkGray" }
        default   { $symbol = "[..]"; $color = "White" }
    }
    
    $componentPadded = $Component.PadRight(16)
    $statusPadded = $Status.PadRight(20)
    
    Write-Host "  " -NoNewline
    Write-Host $symbol -ForegroundColor $color -NoNewline
    Write-Host " $componentPadded" -NoNewline -ForegroundColor White
    Write-Host $statusPadded -ForegroundColor $color -NoNewline
    if ($Detail) {
        Write-Host $Detail -ForegroundColor DarkGray
    } else {
        Write-Host ''
    }
}

function Write-CompleteBanner {
    Write-Host ''
    Write-Host '  ===========================================================' -ForegroundColor Green
    Write-Host '  [OK] All Yonca AI services stopped successfully!' -ForegroundColor Green
    Write-Host '  ===========================================================' -ForegroundColor Green
    Write-Host ''
}

# Main Script

Write-Banner

# 1. Stop FastAPI (Uvicorn)
Write-SectionHeader "Application Servers"

$uvicorn = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*uvicorn*' }
if ($uvicorn) {
    $count = @($uvicorn).Count
    $uvicorn | Stop-Process -Force
    Write-StatusLine "FastAPI" "Stopped" "success" "$count process(es)"
} else {
    Write-StatusLine "FastAPI" "Not running" "skip"
}

# 2. Stop Chainlit UI
$chainlit = Get-Process -Name 'python', 'chainlit' -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like '*chainlit*' -or $_.ProcessName -eq 'chainlit' 
}
if ($chainlit) {
    $count = @($chainlit).Count
    $chainlit | Stop-Process -Force
    Write-StatusLine "Chainlit UI" "Stopped" "success" "$count process(es)"
} else {
    Write-StatusLine "Chainlit UI" "Not running" "skip"
}

# 3. Stop LangGraph Studio (if running)
$langgraph = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like '*langgraph*' 
}
if ($langgraph) {
    $count = @($langgraph).Count
    $langgraph | Stop-Process -Force
    Write-StatusLine "LangGraph" "Stopped" "success" "$count process(es)"
} else {
    Write-StatusLine "LangGraph" "Not running" "skip"
}

# 4. Stop remaining Python processes
$remaining = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if ($remaining) {
    $count = @($remaining).Count
    $remaining | Stop-Process -Force
    Write-StatusLine "Other Python" "Stopped" "warning" "$count process(es)"
} else {
    Write-StatusLine "Other Python" "None found" "skip"
}

# 5. Stop Docker Containers
Write-SectionHeader "Docker Infrastructure"

$containers = docker-compose -f docker-compose.local.yml ps -q 2>$null
if ($containers) {
    docker-compose -f docker-compose.local.yml down 2>$null | Out-Null
    
    Write-StatusLine "PostgreSQL" "Stopped" "success" "yonca-postgres"
    Write-StatusLine "Redis" "Stopped" "success" "yonca-redis"
    Write-StatusLine "Ollama" "Stopped" "success" "yonca-ollama"
    Write-StatusLine "Langfuse DB" "Stopped" "success" "yonca-langfuse-db"
    Write-StatusLine "Langfuse" "Stopped" "success" "yonca-langfuse"
} else {
    Write-StatusLine "Docker" "No containers running" "skip"
}

# Complete
Write-CompleteBanner