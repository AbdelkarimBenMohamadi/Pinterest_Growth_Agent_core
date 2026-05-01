# Pinterest Growth Agent (PGA)

An autonomous AI agent that grows your Pinterest account by finding high-demand keywords, generating optimized pins, and posting them safely — all on autopilot.

## How It Works

```
Research → Generate → Post → Learn → Repeat (daily)
```

1. **Research** — Scrapes Pinterest for trending topics and high-value keywords
2. **Generate** — Creates unique AI images + SEO-optimized metadata
3. **Post** — Publishes pins safely via Playwright with anti-detection
4. **Learn** — Tracks performance and prioritizes what works

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js (for Playwright)

### 2. Setup

```bash
# Clone and enter the project
cd pinterest-growth-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure
cp .env.example .env           # Edit with your API keys
# Edit config.yaml             # Set your niche, keywords, schedule
```

### 3. Run

```bash
# Start the agent
python -m src.main run

# Run once (single cycle, no scheduling)
python -m src.main run --once

# Launch the web dashboard
python -m src.main dashboard

# Check account status
python -m src.main status
```

## Configuration

- **`config.yaml`** — Niche keywords, posting schedule, AI settings, safety limits
- **`.env`** — API keys and Pinterest credentials (never commit this)

## Project Structure

```
src/
├── main.py              # CLI entry point
├── orchestrator.py      # Daily loop controller
├── models.py            # Shared data models
├── brain/               # Research & keyword discovery
├── creator/             # AI image + metadata generation
├── worker/              # Pinterest posting + safety
├── analyzer/            # Performance tracking + learning
├── store/               # SQLite database
├── dashboard/           # Reflex web dashboard (6 pages)
└── utils/               # Config, logging
```

## Docs

- [PRD](prd.md) — What this project does and why
- [Spec](spec.md) — Technical specification and architecture
- [Agent Instructions](AGENTS.md) — Rules for AI agents building this project
