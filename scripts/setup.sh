#!/bin/bash
# Aria Maid System - Linux/Mac Setup Script
# Tested on Python 3.12, Node.js 18+

echo "============================================"
echo "  Aria Maid System - Setup (Linux/Mac)"
echo "============================================"
echo

# Change to project root (parent of scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[*] Working directory: $(pwd)"
echo

# Check Python 3.12
if command -v python3.12 &> /dev/null; then
    PYTHON=python3.12
elif command -v python3 &> /dev/null; then
    PYTHON=python3
else
    echo "[ERROR] Python 3 not found. Please install Python 3.12+"
    echo "Ubuntu/Debian: sudo apt install python3.12 python3.12-venv"
    echo "Mac: brew install python@3.12"
    exit 1
fi

echo "[OK] Python found"
$PYTHON --version

# Create virtual environment
if [ ! -f ".venv/bin/activate" ]; then
    echo
    echo "[*] Creating virtual environment..."
    $PYTHON -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment exists"
fi

# Activate venv and install requirements
echo
echo "[*] Activating virtual environment..."
source .venv/bin/activate

echo "[*] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install requirements"
    exit 1
fi
echo "[OK] Dependencies installed"

# Check for .env file
echo
if [ ! -f ".env" ]; then
    echo "[*] Creating .env from template..."
    cp .env.sample .env
    echo "[!] Please edit .env with your API keys before running"
else
    echo "[OK] .env file exists"
fi

# Create data directory
if [ ! -d "data" ]; then
    echo "[*] Creating data directory..."
    mkdir -p data
fi

echo
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: ./scripts/start.sh"
echo
echo "For Electron desktop avatar (optional):"
echo "  cd desktop/electron"
echo "  npm install"
echo
