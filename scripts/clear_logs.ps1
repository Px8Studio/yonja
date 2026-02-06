# ════════════════════════════════════════════════════════════════════════════
# 🌿 ALİM — Log Cleanup
# ════════════════════════════════════════════════════════════════════════════
# Clears application log files including unified log (alim_unified.log)
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = 'SilentlyContinue'

$projectRoot = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $projectRoot "logs"

Write-Host "`n🧹 ALİM — Log Cleanup" -ForegroundColor Cyan

# Ensure logs directory exists (create if not)
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "   → Created logs directory" -ForegroundColor DarkGray
}

# Clear unified log specifically (truncate instead of delete for live watchers)
$unifiedLog = Join-Path $logDir "alim_unified.log"
if (Test-Path $unifiedLog) {
    "" | Set-Content $unifiedLog -Force
    Write-Host "   → Cleared unified log (alim_unified.log)" -ForegroundColor Green
}

# Clear all other log files
$files = Get-ChildItem -Path $logDir -Include *.log, *.txt -Recurse -Exclude "alim_unified.log"
if ($files) {
    $files | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   → Cleared $($files.Count) additional log file(s)" -ForegroundColor Green
}
else {
    Write-Host "   → No additional log files to clear" -ForegroundColor DarkGray
}

Write-Host "✅ Log cleanup complete" -ForegroundColor Green
