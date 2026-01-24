# ════════════════════════════════════════════════════════════════════════════
# 🌿 YONCA AI — Force Cleanup
# ════════════════════════════════════════════════════════════════════════════
# Kills lingering processes that might hold onto ports (8000, 8501, etc.)
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = 'SilentlyContinue'

Write-Host "`n🧹 YONCA AI — Port Cleanup" -ForegroundColor Cyan
Write-Host "Checking for lingering processes (Python, Chainlit, LangGraph)..." -ForegroundColor DarkGray

$targets = "python", "chainlit", "langgraph"
$count = 0

foreach ($target in $targets) {
    # Check for process
    $procs = Get-Process -Name $target -ErrorAction SilentlyContinue

    if ($procs) {
        foreach ($p in $procs) {
            # Try to stop gracefuly first, then force
            Write-Host "   → Stopping $target (PID: $($p.Id))..." -NoNewline -ForegroundColor Yellow
            $p | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host " ✅" -ForegroundColor Green
            $count++
        }
    }
}

if ($count -gt 0) {
    Write-Host "`n🧹 Forcefully cleared $count process(es)" -ForegroundColor Green
} else {
    Write-Host "✨ Ports are clean (No lingering Python/Chainlit processes found)" -ForegroundColor Gray
}

# ════════════════════════════════════════════════════════════════════════════
# 📂 Log Cleanup
# ════════════════════════════════════════════════════════════════════════════
$logDir = Join-Path $PSScriptRoot "..\logs"
if (Test-Path $logDir) {
    Write-Host "`n🧹 Cleaning logs directory..." -ForegroundColor Cyan
    Get-ChildItem -Path $logDir -Include *.log, *.txt -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   → Logs cleared" -ForegroundColor Green
}

# ════════════════════════════════════════════════════════════════════════════
# 🌐 Browser Cache Cleanup
# ════════════════════════════════════════════════════════════════════════════
$cacheScript = Join-Path $PSScriptRoot "clear_browser_cache.ps1"
if (Test-Path $cacheScript) {
    & $cacheScript
}
