# ════════════════════════════════════════════════════════════════════════════
# 🧹 Clear Browser Cache
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = 'SilentlyContinue'
Write-Host "`n🧹 ALİM — Browser Cache Cleanup" -ForegroundColor Cyan

$cleared = 0

$browsers = @{
    'Chrome' = 'Google\Chrome\User Data\Default'
    'Edge'   = 'Microsoft\Edge\User Data\Default'
    'Brave'  = 'BraveSoftware\Brave-Browser\User Data\Default'
}

foreach ($browser in $browsers.GetEnumerator()) {
    $browserName = $browser.Key
    $browserPath = $browser.Value

    $paths = @(
        "$env:APPDATA\$browserPath\Cache",
        "$env:APPDATA\$browserPath\Code Cache",
        "$env:LOCALAPPDATA\$browserPath\Cache",
        "$env:LOCALAPPDATA\$browserPath\Code Cache"
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            Write-Host "   → Clearing $browserName cache..." -NoNewline -ForegroundColor Yellow
            Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host " ✅" -ForegroundColor Green
            $cleared++
        }
    }
}

if ($cleared -gt 0) {
    Write-Host "`n✨ Cleared $cleared cache locations." -ForegroundColor Green
}
else {
    Write-Host "✨ No browser cache found to clear." -ForegroundColor Gray
}
