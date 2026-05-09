#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

echo "Running forced test cycle. Safety limits and schedule waiting are bypassed."
python -m src.main run-now --force
