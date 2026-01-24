# scripts/health_check.ps1
# Health check script for Yonca AI development stack
# Checks all services and reports status

param(
    [switch]$Wait,
    [int]$Timeout = 60,
    [switch]$Quiet
)

$ErrorActionPreference = "Continue"

function Write-Status {
    param([string]$Service, [string]$Status, [string]$Details = "")

    $icon = switch ($Status) {
        "OK" { "✅" }
        "FAIL" { "❌" }
        "WARN" { "⚠️" }
        "WAIT" { "⏳" }
        default { "❓" }
    }

    if (-not $Quiet) {
        $msg = "$icon $Service`: $Status"
        if ($Details) { $msg += " ($Details)" }
        Write-Host $msg
    }
}

function Test-Docker {
    try {
        $result = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Docker" "OK" "Running"
            return $true
        }
    }
    catch {}
    Write-Status "Docker" "FAIL" "Not running"
    return $false
}

function Test-Container {
    param([string]$Name)

    try {
        $status = docker inspect --format='{{.State.Status}}' $Name 2>&1
        if ($status -eq "running") {
            Write-Status "Container: $Name" "OK" "Running"
            return $true
        }
        else {
            Write-Status "Container: $Name" "FAIL" $status
            return $false
        }
    }
    catch {
        Write-Status "Container: $Name" "FAIL" "Not found"
        return $false
    }
}

function Test-Endpoint {
    param([string]$Name, [string]$Url, [int]$ExpectedStatus = 200)

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Status $Name "OK" "HTTP $($response.StatusCode)"
            return $true
        }
    }
    catch {
        Write-Status $Name "FAIL" $_.Exception.Message
    }
    return $false
}

function Test-OllamaModels {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
        $models = $response.models | ForEach-Object { $_.name }
        if ($models -contains "qwen3:4b" -or $models -contains "atllama") {
            Write-Status "Ollama Models" "OK" ($models -join ", ")
            return $true
        }
        else {
            Write-Status "Ollama Models" "WARN" "No required models found"
            return $false
        }
    }
    catch {
        Write-Status "Ollama Models" "FAIL" "Cannot query models"
        return $false
    }
}

# Main health check
if (-not $Quiet) {
    Write-Host ""
    Write-Host "🌿 YONCA AI — Health Check" -ForegroundColor Green
    Write-Host "=" * 40
    Write-Host ""
}

$allHealthy = $true

# 1. Docker
if (-not (Test-Docker)) { $allHealthy = $false }

# 2. Containers
if (-not (Test-Container "alim-ollama")) { $allHealthy = $false }
if (-not (Test-Container "alim-redis")) { $allHealthy = $false }

# 3. Ollama API
if (-not (Test-Endpoint "Ollama API" "http://localhost:11434/api/tags")) { $allHealthy = $false }

# 4. Ollama Models
if (-not (Test-OllamaModels)) { $allHealthy = $false }

# 5. Redis (via Docker exec ping)
try {
    $redisPing = docker exec alim-redis redis-cli ping 2>&1
    if ($redisPing -eq "PONG") {
        Write-Status "Redis" "OK" "PONG"
    }
    else {
        Write-Status "Redis" "FAIL" $redisPing
        $allHealthy = $false
    }
}
catch {
    Write-Status "Redis" "FAIL" "Cannot ping"
    $allHealthy = $false
}

# 6. FastAPI (if running)
$apiCheck = Test-Endpoint "FastAPI" "http://localhost:8000/health"

# 7. Chainlit (if running)
$uiCheck = Test-Endpoint "Chainlit UI" "http://localhost:8501"

if (-not $Quiet) {
    Write-Host ""
    Write-Host "=" * 40
    if ($allHealthy) {
        Write-Host "✅ Core services healthy" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Some services unhealthy" -ForegroundColor Red
    }
    Write-Host ""
}

# Exit with appropriate code
if ($allHealthy) { exit 0 } else { exit 1 }
