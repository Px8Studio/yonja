# ════════════════════════════════════════════════════════════════════════════
# 🧹 Clear Browser Cache
# ════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = 'SilentlyContinue'
$cleared = 0

$browsers = @{
    'Chrome' = 'Google\Chrome\User Data\Default'
    'Edge'   = 'Microsoft\Edge\User Data\Default'
    'Brave'  = 'BraveSoftware\Brave-Browser\User Data\Default'
}

foreach ($browser in $browsers.GetEnumerator()) {
    $paths = @(
        "$env:APPDATA\$($browser.Value)\Cache",
        "$env:APPDATA\$($browser.Value)\Code Cache",
        "$env:LOCALAPPDATA\$($browser.Value)\Cache",
        "$env:LOCALAPPDATA\$($browser.Value)\Code Cache"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            Remove-Item $path -Recurse -Force
            $cleared++
        }
    }
}

Write-Host "🧹 Browser cache cleared ($cleared items)" -ForegroundColor Green