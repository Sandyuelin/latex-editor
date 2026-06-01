#!/bin/bash
# One-click launcher for LaTeX Editor

echo "=== LaTeX Editor Launcher ==="
cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ python3 not found. Please install Python 3."
  exit 1
fi

# Create venv if needed
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install flask if needed
python3 -c "import flask" 2>/dev/null || {
  echo "📦 Installing Flask..."
  pip install flask -q
}

# Check pdflatex
if ! command -v pdflatex &>/dev/null; then
  echo ""
  echo "⚠️  pdflatex not found — PDF compilation won't work."
  echo "   Install BasicTeX:  brew install --cask basictex"
  echo "   Then run:          sudo tlmgr update --self && sudo tlmgr install collection-latex"
  echo ""
fi

# Open browser after a short delay
(sleep 1.5 && open http://localhost:8080) &

echo "🚀 Starting server at http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""

python3 app.py
