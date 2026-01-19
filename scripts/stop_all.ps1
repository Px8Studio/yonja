# ════════════════════════════════════════════════════════════════════════════
# 🌿 YONCA AI — Stop All Services
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = 'SilentlyContinue'

Write-Host "`n🛑 YONCA AI — Stopping Services`n" -ForegroundColor Yellow

# Stop Python services
$stopped = @()

$python = Get-Process -Name 'python' -ErrorAction SilentlyContinue
if ($python) {
    $python | Stop-Process -Force
    $stopped += "Python ($(@($python).Count))"
}

$chainlit = Get-Process -Name 'chainlit' -ErrorAction SilentlyContinue  
if ($chainlit) {
    $chainlit | Stop-Process -Force
    $stopped += "Chainlit ($(@($chainlit).Count))"
}

$langgraph = Get-Process -Name 'langgraph' -ErrorAction SilentlyContinue
if ($langgraph) {
    $langgraph | Stop-Process -Force
    $stopped += "LangGraph ($(@($langgraph).Count))"
}

if ($stopped.Count -gt 0) {
    Write-Host "✅ Stopped: $($stopped -join ', ')" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No Python processes found" -ForegroundColor DarkGray
}

# Stop Docker
Write-Host "🐳 Stopping Docker containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml down 2>$null | Out-Null
Write-Host "✅ Docker containers stopped" -ForegroundColor Green

Write-Host "`n✅ All services stopped!`n" -ForegroundColor Green
