#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

echo "Running one on-demand agent cycle."
python -m src.main run-now --schedule-mode immediate
