#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Pinterest Growth Agent - Pre-Flight Check"

if [ ! -d venv ]; then
  echo "FAIL: venv not found. Run ./01-install.sh first."
  exit 1
fi

source venv/bin/activate

python --version
python -m pip show playwright >/dev/null
python -m pip show apscheduler >/dev/null
python -m playwright install chromium --dry-run >/dev/null

test -f config.yaml || { echo "FAIL: config.yaml not found"; exit 1; }
test -f .env || { echo "FAIL: .env not found"; exit 1; }

python -m src.main stats >/dev/null

echo "All basic checks passed."
