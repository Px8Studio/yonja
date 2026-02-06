# ════════════════════════════════════════════════════════════════════════════
# 🌿 ALİM — Unified Log Aggregator
# ════════════════════════════════════════════════════════════════════════════
# Streams all service logs to a single file for unified debugging.
#
# Usage:
#   ./scripts/unified_log.ps1                  # Start fresh, watch logs
#   ./scripts/unified_log.ps1 -Clear           # Clear and start fresh
#   ./scripts/unified_log.ps1 -Tail 100        # Show last 100 lines
#
# The unified log file is: logs/alim_unified.log
# All services append to this file with [SERVICE] prefixes.
# ════════════════════════════════════════════════════════════════════════════

param (
    [switch]$Clear = $false,
    [int]$Tail = 0,
    [switch]$Watch = $false
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$logsDir = Join-Path $projectRoot "logs"
$unifiedLog = Join-Path $logsDir "alim_unified.log"

# Ensure logs directory exists
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "📁 Created logs directory: $logsDir" -ForegroundColor Green
}

# Clear log if requested
if ($Clear) {
    if (Test-Path $unifiedLog) {
        Remove-Item $unifiedLog -Force
        Write-Host "🧹 Cleared unified log" -ForegroundColor Yellow
    }
    "" | Set-Content $unifiedLog
}

# Ensure log file exists
if (-not (Test-Path $unifiedLog)) {
    "" | Set-Content $unifiedLog
}

# Show tail if requested
if ($Tail -gt 0) {
    if (Test-Path $unifiedLog) {
        Get-Content $unifiedLog -Tail $Tail
    }
    else {
        Write-Host "📭 No logs yet" -ForegroundColor DarkGray
    }
    exit 0
}

# Watch mode - continuously tail the log
if ($Watch) {
    Write-Host "👁️ Watching unified log: $unifiedLog" -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop" -ForegroundColor DarkGray
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Get-Content $unifiedLog -Wait -Tail 50
    exit 0
}

# Default: show status and path
Write-Host ""
Write-Host "  🌿 ALİM Unified Logging" -ForegroundColor Cyan
Write-Host "  ════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  📄 Log file: $unifiedLog" -ForegroundColor White
if (Test-Path $unifiedLog) {
    $size = (Get-Item $unifiedLog).Length
    $lines = (Get-Content $unifiedLog | Measure-Object -Line).Lines
    Write-Host "  📊 Size: $([math]::Round($size/1024, 2)) KB ($lines lines)" -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "  Commands:" -ForegroundColor Yellow
Write-Host "    ./scripts/unified_log.ps1 -Watch        # Live stream" -ForegroundColor DarkGray
Write-Host "    ./scripts/unified_log.ps1 -Tail 200     # Last 200 lines" -ForegroundColor DarkGray
Write-Host "    ./scripts/unified_log.ps1 -Clear        # Clear and start fresh" -ForegroundColor DarkGray
Write-Host ""
