# scripts/pre-start-checks.ps1
# ═══════════════════════════════════════════════════════════════════════════
# ⚡ Yonca AI — Pre-Start Quality Checks
# ═══════════════════════════════════════════════════════════════════════════
#
# Purpose: Run fast quality checks BEFORE starting services
# Called by "Start All" task to catch breaking changes early
#
# Checks (in order of speed):
#   1. 🔍 Ruff linting (< 2s) — AUTO-FIXES when possible
#   2. ✅ Import validation (< 1s)
#   3. 🧪 Critical unit tests (< 10s)
#   4. ⚙️ Config validation (< 1s)
#
# If ANY check fails → BLOCK startup (after attempting auto-fixes)
#
# ═══════════════════════════════════════════════════════════════════════════

param(
    [switch]$Quick = $false,     # Skip tests, only lint
    [switch]$Verbose = $false,
    [switch]$NoAutoFix = $false  # Disable automatic fixes
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "⚡ Pre-Start Quality Checks" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$checksPassed = $true
$checksRun = 0

# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

function Test-Check {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    $script:checksRun++
    Write-Host "[$script:checksRun] $Name..." -ForegroundColor Yellow -NoNewline

    try {
        $output = & $Command 2>&1
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0 -or $null -eq $exitCode) {
            Write-Host " ✅" -ForegroundColor Green
            if ($Verbose -and $output) {
                Write-Host $output -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host " ❌ FAILED" -ForegroundColor Red
            Write-Host $output -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ❌ ERROR" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# Check 1: Ruff Linting (Fast - ~2s) with AUTO-FIX
# ═══════════════════════════════════════════════════════════════════════════

$ruffCmd = if (Test-Path ".venv/Scripts/ruff.exe") {
    ".venv/Scripts/ruff.exe"
} else {
    "ruff"
}

# First pass: Check for issues
$lintPassed = Test-Check -Name "🔍 Ruff linting" -Command {
    & $ruffCmd check src/ tests/ --quiet
}

# If failed and auto-fix is enabled, attempt to fix
if (-not $lintPassed -and -not $NoAutoFix) {
    Write-Host ""
    Write-Host "🔧 Attempting automatic fixes (including unsafe modernizations)..." -ForegroundColor Yellow

    $fixOutput = & $ruffCmd check src/ tests/ --fix --unsafe-fixes 2>&1
    $fixExitCode = $LASTEXITCODE

    if ($fixExitCode -eq 0) {
        Write-Host "✅ Auto-fixed all issues!" -ForegroundColor Green
        $lintPassed = $true
    } else {
        Write-Host "⚠️  Fixed some issues, but manual intervention needed:" -ForegroundColor Yellow
        Write-Host $fixOutput -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Remaining issues require manual fixes:" -ForegroundColor Yellow
        Write-Host "   • F841 (unused variables): Remove or prefix with _" -ForegroundColor Gray
        Write-Host "   • E722 (bare except): Specify exception type" -ForegroundColor Gray
        $checksPassed = $false
    }
} elseif (-not $lintPassed) {
    Write-Host ""
    Write-Host "💡 Run with auto-fix: $ruffCmd check src/ tests/ --fix --unsafe-fixes" -ForegroundColor Yellow
    $checksPassed = $false
}

# ═══════════════════════════════════════════════════════════════════════════
# Check 2: Import Validation (Very Fast - ~1s)
# ═══════════════════════════════════════════════════════════════════════════

$pythonCmd = if (Test-Path ".venv/Scripts/python.exe") {
    ".venv/Scripts/python.exe"
} else {
    "python"
}

$importPassed = Test-Check -Name "✅ Import validation" -Command {
    $env:PYTHONPATH = "$PWD/src"
    $env:PYTHONIOENCODING = "utf-8"
    & $pythonCmd -c @"
import sys
sys.path.insert(0, 'src')
try:
    from yonca.config import settings
    from yonca.llm.factory import get_llm_provider
    from yonca.agent.graph import compile_agent_graph
    from yonca.api.main import app
    print('Core imports OK')
except Exception as e:
    print(f'Import error: {e}', file=sys.stderr)
    sys.exit(1)
"@
}

if (-not $importPassed) {
    Write-Host ""
    Write-Host "💡 Fix import errors before starting services" -ForegroundColor Yellow
    $checksPassed = $false
}

# ═══════════════════════════════════════════════════════════════════════════
# Check 3: Critical Unit Tests (Fast - ~10s)
# ═══════════════════════════════════════════════════════════════════════════

$pytestCmd = if (Test-Path ".venv/Scripts/pytest.exe") {
    ".venv/Scripts/pytest.exe"
} else {
    "pytest"
}

if (-not $Quick) {
    $testPassed = Test-Check -Name "🧪 Critical unit tests" -Command {
        $env:PYTHONPATH = "$PWD/src"
        & $pytestCmd tests/unit/ -v --tb=short -q --maxfail=1
    }

    if (-not $testPassed) {
        Write-Host ""
        Write-Host "💡 Fix failing tests before starting services" -ForegroundColor Yellow
        Write-Host "   Run: pytest tests/unit/ -v" -ForegroundColor Gray
        $checksPassed = $false
    }
} else {
    Write-Host "[Skipped] 🧪 Unit tests (--Quick mode)" -ForegroundColor Gray
}

# ═══════════════════════════════════════════════════════════════════════════
# Check 4: Config Validation (Very Fast - ~1s)
# ═══════════════════════════════════════════════════════════════════════════

$configPassed = Test-Check -Name "⚙️ Config validation" -Command {
    $env:PYTHONPATH = "$PWD/src"
    $env:PYTHONIOENCODING = "utf-8"
    & $pythonCmd -c @"
from yonca.config import settings
import os

# Check critical settings
assert settings.database_url, 'DATABASE_URL not set'
assert settings.llm_provider, 'LLM provider not configured'

# Check for common mistakes
if 'your_key_here' in str(settings.groq_api_key or ''):
    raise ValueError('Groq API key is placeholder - set YONCA_GROQ_API_KEY')

print('Config valid')
"@
}

if (-not $configPassed) {
    Write-Host ""
    Write-Host "💡 Check .env file for missing/invalid values" -ForegroundColor Yellow
    $checksPassed = $false
}

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

$elapsed = (Get-Date) - $startTime
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($checksPassed) {
    Write-Host "✅ All checks passed! ($($elapsed.TotalSeconds.ToString('F1'))s)" -ForegroundColor Green
    Write-Host "   Safe to start services" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    exit 0
} else {
    Write-Host "❌ Quality checks FAILED! ($($elapsed.TotalSeconds.ToString('F1'))s)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🛑 BLOCKING SERVICE START" -ForegroundColor Red
    Write-Host "   Fix the issues above before continuing" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To skip checks (NOT recommended):" -ForegroundColor Gray
    Write-Host "   1. Comment out pre-checks in .vscode/tasks.json" -ForegroundColor Gray
    Write-Host "   2. Or run: pwsh scripts/pre-start-checks.ps1 -Quick" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
