# ═══════════════════════════════════════════════════════════════════════════
# 🌿 Yonca AI - Quick Environment Activation
# ═══════════════════════════════════════════════════════════════════════════
# Usage: 
#   .\activate.ps1        # Activate Poetry shell
#   .\activate.ps1 -Info  # Show available commands
# ═══════════════════════════════════════════════════════════════════════════

param(
    [switch]$Info
)

if ($Info) {
    Write-Host "`n🌿 Yonca AI Development Environment" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    
    Write-Host "`n📦 Option 1: Use Poetry Shell (Recommended)" -ForegroundColor Yellow
    Write-Host "   poetry shell                  # Activate environment"
    Write-Host "   uvicorn yonca.api.main:app --reload"
    Write-Host "   alembic upgrade head"
    Write-Host "   chainlit run demo-ui/app.py"
    
    Write-Host "`n⚡ Option 2: Use Poetry Run (No activation needed)" -ForegroundColor Yellow
    Write-Host "   poetry run dev                # Start FastAPI"
    Write-Host "   poetry run migrate            # Run migrations"
    Write-Host "   poetry run seed               # Seed database"
    Write-Host "   poetry run pytest             # Run tests"
    
    Write-Host "`n🎯 Option 3: Use Full Paths" -ForegroundColor Yellow
    Write-Host "   .\.venv\Scripts\python.exe -m uvicorn yonca.api.main:app --reload"
    Write-Host "   .\.venv\Scripts\alembic.exe upgrade head"
    
    Write-Host "`n═══════════════════════════════════════════════════════════════`n" -ForegroundColor DarkGray
    exit 0
}

# Main activation
Write-Host "`n🌿 Activating Yonca AI environment..." -ForegroundColor Cyan

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "✓ Using existing virtual environment" -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  No .venv found. Creating with Poetry..." -ForegroundColor Yellow
    poetry install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Environment created!" -ForegroundColor Green
        & .\.venv\Scripts\Activate.ps1
    } else {
        Write-Host "❌ Failed to create environment" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ Environment activated! Available commands:" -ForegroundColor Green
Write-Host "   uvicorn yonca.api.main:app --reload   # Start API"
Write-Host "   alembic upgrade head                  # Run migrations"
Write-Host "   chainlit run demo-ui/app.py           # Start UI"
Write-Host "`n   Run '.\activate.ps1 -Info' for more options`n"
