#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting the daily scheduler. Press Ctrl+C to stop."
python -m src.main start
