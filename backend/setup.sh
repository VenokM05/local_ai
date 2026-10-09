#!/usr/bin/env bash
# One-time setup: create an isolated venv and install backend deps locally.
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Backend deps installed. Next steps:"
echo "  1. Install Ollama:  brew install ollama"
echo "  2. Start runtime:   ollama serve   (leave running)"
echo "  3. Pull small model: ollama pull llama3.2:3b"
echo "  4. Run API:         ./run.sh"
