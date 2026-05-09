#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Pinterest Growth Agent - Install"
echo "Creating virtual environment..."
python3 -m venv venv

source venv/bin/activate

echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Installing Playwright Chromium browser..."
python -m playwright install chromium

mkdir -p data assets
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "Install complete. Edit .env and config.yaml, then run ./02-validate.sh."
