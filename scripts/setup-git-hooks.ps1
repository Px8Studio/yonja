# scripts/setup-git-hooks.ps1
# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ ALİM — Git Hooks Setup Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Purpose: Install pre-commit hooks for automatic quality checks
#
# What it does:
#   1. Installs pre-commit package (if not already installed)
#   2. Sets up git hooks from .pre-commit-config.yaml
#   3. Optionally runs initial check on all files
#
# Usage:
#   pwsh scripts/setup-git-hooks.ps1
#   pwsh scripts/setup-git-hooks.ps1 -CheckAll  # Also run on existing files
#
# ═══════════════════════════════════════════════════════════════════════════

param(
    [switch]$CheckAll = $false
)

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🛡️  ALİM — Git Hooks Setup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if pre-commit is installed
Write-Host "📋 Checking pre-commit installation..." -ForegroundColor Yellow
$precommitInstalled = $null -ne (Get-Command pre-commit -ErrorAction SilentlyContinue)

if (-not $precommitInstalled) {
    Write-Host "❌ pre-commit not found. Installing..." -ForegroundColor Red

    # Use venv python if available, otherwise global
    $pythonCmd = if (Test-Path ".venv/Scripts/python.exe") {
        ".venv/Scripts/python.exe"
    }
    else {
        "python"
    }

    & $pythonCmd -m pip install pre-commit

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install pre-commit" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ pre-commit installed successfully" -ForegroundColor Green
}
else {
    Write-Host "✅ pre-commit already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Installing git hooks..." -ForegroundColor Yellow

# Use venv pre-commit if available
$precommitCmd = if (Test-Path ".venv/Scripts/pre-commit.exe") {
    ".venv/Scripts/pre-commit.exe"
}
else {
    "pre-commit"
}

# Install hooks
& $precommitCmd install --install-hooks

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install hooks" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Git hooks installed successfully" -ForegroundColor Green

# Optionally run on all files
if ($CheckAll) {
    Write-Host ""
    Write-Host "📋 Running hooks on all files (this may take a minute)..." -ForegroundColor Yellow
    & $precommitCmd run --all-files

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "⚠️  Some checks failed. Fix the issues above and commit again." -ForegroundColor Yellow
        Write-Host "   Or skip hooks temporarily with: git commit --no-verify" -ForegroundColor Gray
    }
    else {
        Write-Host "✅ All checks passed!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "From now on, every commit will automatically run:" -ForegroundColor White
Write-Host "  • 🔍 Ruff linter + formatter" -ForegroundColor Gray
Write-Host "  • 🧹 File hygiene checks" -ForegroundColor Gray
Write-Host "  • 🔐 Secret detection" -ForegroundColor Gray
Write-Host ""
Write-Host "To skip hooks temporarily (NOT recommended):" -ForegroundColor Yellow
Write-Host "  git commit --no-verify" -ForegroundColor Gray
Write-Host ""
Write-Host "To run manually:" -ForegroundColor White
Write-Host "  pre-commit run --all-files" -ForegroundColor Gray
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
