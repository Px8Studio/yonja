#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# 🖥️ Demo UI Setup Script (Linux/Mac)
# ═══════════════════════════════════════════════════════════════════════════

echo "🌿 Setting up Demo UI..."

# Check if we're in demo-ui folder
if [ ! -f "app.py" ]; then
    echo "❌ Error: Must run from demo-ui/ folder"
    echo "   cd demo-ui"
    echo "   ./setup.sh"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate and install dependencies
echo "📥 Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Demo UI setup complete!"
echo ""
echo "To activate the environment:"
echo "   cd demo-ui"
echo "   source .venv/bin/activate"
echo ""
echo "To run Chainlit:"
echo "   chainlit run app.py -w --port 8501"
