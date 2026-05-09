#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

echo "Running one cycle in headless browser mode."
python -m src.main run-now --browser-mode headless --schedule-mode immediate
