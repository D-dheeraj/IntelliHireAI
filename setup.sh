#!/bin/bash

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       🧠 IntelliHire AI Setup        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Go to project root
cd "$(dirname "$0")"

# ── Step 1: Check Python ────────────────────────────────────────────────────
echo "🔍 Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 not found! Install from https://python.org"
    exit 1
fi
echo "✅ Python found: $(python3 --version)"

# ── Step 2: Create virtual environment ──────────────────────────────────────
echo ""
echo "📦 Setting up virtual environment..."

if command -v uv &>/dev/null; then
    uv venv --python 3.11 --clear 2>/dev/null || uv venv --clear
    uv sync
    PYTHON=".venv/bin/python"
    STREAMLIT=".venv/bin/streamlit"
else
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet streamlit google-genai google-generativeai pandas plotly psycopg2-binary pypdf python-dotenv sqlalchemy
    PYTHON=".venv/bin/python"
    STREAMLIT=".venv/bin/streamlit"
fi
echo "✅ Dependencies installed!"

# ── Step 3: Setup .env ──────────────────────────────────────────────────────
echo ""
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
GOOGLE_API_KEY=your_google_api_key_here
# DATABASE_URL=postgresql://admin:admin123@localhost:5432/intellihire
# Leave DATABASE_URL empty to use SQLite (no Docker needed)
EOF
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  ⚠️  ACTION REQUIRED: Add your Google API Key!       ║"
    echo "║                                                      ║"
    echo "║  1. Open the file: .env                              ║"
    echo "║  2. Replace 'your_google_api_key_here' with your key ║"
    echo "║  3. Get key at: https://aistudio.google.com/apikey   ║"
    echo "║  4. Run this script again: bash setup.sh             ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    exit 0
fi

# Check if API key is still placeholder
if grep -q "your_google_api_key_here" .env; then
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  ❌ Please add your Google API Key in .env first!    ║"
    echo "║  Get key at: https://aistudio.google.com/apikey     ║"
    echo "╚══════════════════════════════════════════════════════╝"
    exit 1
fi

echo "✅ .env file found!"

# ── Step 4: Create DB tables ────────────────────────────────────────────────
echo ""
echo "🗄️  Setting up database..."
$PYTHON create_tables.py
echo "✅ Database ready!"

# ── Step 5: Launch app ──────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║  🚀 Launching IntelliHire AI...      ║"
echo "║  Open: http://localhost:8501         ║"
echo "╚══════════════════════════════════════╝"
echo ""

$STREAMLIT run app/streamlit_app.py --server.port 8501
