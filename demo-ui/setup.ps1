# ═══════════════════════════════════════════════════════════════════════════
# 🖥️ Demo UI Setup Script
# ═══════════════════════════════════════════════════════════════════════════
# Creates an isolated virtual environment for Chainlit frontend
# Run this once after cloning the repo

Write-Host "🌿 Setting up Demo UI..." -ForegroundColor Green

# Check if we're in demo-ui folder
if (-not (Test-Path "app.py")) {
    Write-Host "❌ Error: Must run from demo-ui/ folder" -ForegroundColor Red
    Write-Host "   cd demo-ui" -ForegroundColor Yellow
    Write-Host "   .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
python -m venv .venv

# Activate and install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "✅ Demo UI setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment:" -ForegroundColor Yellow
Write-Host "   cd demo-ui" -ForegroundColor White
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run Chainlit:" -ForegroundColor Yellow
Write-Host "   chainlit run app.py -w --port 8501" -ForegroundColor White
