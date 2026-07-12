#!/bin/bash
# setup.sh
# One-command setup for CoreMind on Mac/Linux.
# Usage: chmod +x setup.sh && ./setup.sh

echo "=== CoreMind Setup ==="

echo -e "\nInstalling Python dependencies..."
pip install -r requirements.txt

echo -e "\nChecking for Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Please install it from https://ollama.com/download"
    echo "Then re-run this script."
    exit 1
fi

echo -e "\nChecking for phi3:mini model..."
if ! ollama list | grep -q "phi3:mini"; then
    echo "Pulling phi3:mini (about 2.3GB, may take a few minutes)..."
    ollama pull phi3:mini
else
    echo "phi3:mini already present."
fi

echo -e "\nSetup complete. Launching CoreMind..."
python -m streamlit run app.py
