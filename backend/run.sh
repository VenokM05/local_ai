#!/usr/bin/env bash
# Start the local API server (loopback only).
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
exec python app.py
