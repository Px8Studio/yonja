# ════════════════════════════════════════════════════════════════════════════
# 🌿 ALİM — Log Cleanup
# ════════════════════════════════════════════════════════════════════════════
# Clears application log files
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = 'SilentlyContinue'

$logDir = Join-Path $PSScriptRoot "..\logs"
if (Test-Path $logDir) {
    Write-Host "`n🧹 ALİM — Log Cleanup" -ForegroundColor Cyan
    Write-Host "Cleaning logs directory ($logDir)..." -ForegroundColor DarkGray

    $files = Get-ChildItem -Path $logDir -Include *.log, *.txt -Recurse
    if ($files) {
        $files | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "   → Logs cleared ($( $files.Count ) files removed)" -ForegroundColor Green
    }
    else {
        Write-Host "✨ No log files found to clear." -ForegroundColor Gray
    }
}
else {
    Write-Host "⚠️ Log directory not found at $logDir" -ForegroundColor Yellow
}
