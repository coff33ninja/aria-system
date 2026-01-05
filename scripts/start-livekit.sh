#!/bin/bash
# Aria Maid System - Linux/Mac LiveKit Mode Start Script

echo "============================================"
echo "  Aria Maid System - LiveKit Mode"
echo "============================================"
echo

# Change to project root (parent of scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[*] Working directory: $(pwd)"

# Check if venv exists
if [ ! -f ".venv/bin/activate" ]; then
    echo
    echo "[ERROR] Virtual environment not found."
    echo "Please run: ./scripts/setup.sh"
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Check for .env
if [ ! -f ".env" ]; then
    echo
    echo "[ERROR] .env file not found."
    echo "Please copy .env.sample to .env and add your API keys."
    exit 1
fi

echo "[OK] Environment ready"
echo
echo "[*] Starting Aria LiveKit Mode..."
echo
echo "Requires LiveKit credentials in .env"
echo "Press Ctrl+C to stop"
echo

python -m livekit_mode.agent dev
