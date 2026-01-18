# Stop All Yonca AI Services

$ErrorActionPreference = 'SilentlyContinue'

Write-Host ''
Write-Host '═══════════════════════════════════════════════════════' -ForegroundColor Magenta
Write-Host '  🛑 YONCA AI - Stopping All Services' -ForegroundColor Magenta
Write-Host '═══════════════════════════════════════════════════════' -ForegroundColor Magenta
Write-Host ''

Write-Host '🌿 [1/4] Stopping FastAPI (uvicorn)...' -ForegroundColor Yellow
$uvicorn = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*uvicorn*' }
if ($uvicorn) {
    $uvicorn | Stop-Process -Force
    Write-Host '   ✅ FastAPI stopped' -ForegroundColor Green
} else {
    Write-Host '   ⚪ FastAPI was not running' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '🖥️ [2/4] Stopping Chainlit UI...' -ForegroundColor Yellow
$chainlit = Get-Process -Name 'python', 'chainlit' -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*chainlit*' -or $_.ProcessName -eq 'chainlit' }
if ($chainlit) {
    $chainlit | Stop-Process -Force
    Write-Host '   ✅ Chainlit stopped' -ForegroundColor Green
} else {
    Write-Host '   ⚪ Chainlit was not running' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '🐍 [3/4] Stopping remaining Python processes...' -ForegroundColor Yellow
$remaining = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if ($remaining) {
    $count = $remaining.Count
    $remaining | Stop-Process -Force
    Write-Host "   ✅ Stopped $count Python process(es)" -ForegroundColor Green
} else {
    Write-Host '   ⚪ No other Python processes' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '🐳 [4/4] Stopping Docker containers...' -ForegroundColor Yellow
$containers = docker-compose -f docker-compose.local.yml ps -q 2>$null
if ($containers) {
    docker-compose -f docker-compose.local.yml down 2>$null
    Write-Host '   ✅ Docker containers stopped' -ForegroundColor Green
} else {
    Write-Host '   ⚪ No Docker containers running' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '═══════════════════════════════════════════════════════' -ForegroundColor Green
Write-Host '  ✅ ALL SERVICES STOPPED' -ForegroundColor Green
Write-Host '═══════════════════════════════════════════════════════' -ForegroundColor Green
Write-Host ''