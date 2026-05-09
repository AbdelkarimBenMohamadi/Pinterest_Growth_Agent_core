#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

echo "Running one cycle in GUI browser mode."
python -m src.main run-now --browser-mode gui --schedule-mode immediate
