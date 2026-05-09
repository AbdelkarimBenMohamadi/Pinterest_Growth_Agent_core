# Social Media Growth Agent (PGA)

An autonomous AI agent that grows your social media presence (Pinterest, Facebook, Instagram, Twitter) by finding high-demand keywords, generating optimized content, and posting safely — all on autopilot.

## How It Works

```
Research → Generate → Post → Learn → Repeat (daily)
```

1. **Research** — Scrapes Pinterest, Facebook, Instagram, and Twitter for trending topics and high-value keywords
2. **Generate** — Creates unique AI images + SEO-optimized metadata
3. **Post** — Publishes pins safely via Playwright with anti-detection
4. **Learn** — Tracks performance and prioritizes what works

---

## Quick Start with Batch Files (Beginners)

Double-click these files in order — no command line needed:

| File | What It Does |
|---|---|
| **`01-install.bat`** | One-click install — Python environment, dependencies, Playwright |
| **`02-validate.bat`** | Checks everything is ready before you run |
| **`03-test-mode.bat`** | First-time test — does one full cycle, bypasses safety limits |
| **`04-run-once.bat`** | Normal on-demand run — respects safety limits |
| **`05-status.bat`** | View recent stats and keyword performance |
| **`06-start-scheduler.bat`** | Start the daily scheduler — runs forever in background |

### First Time Setup

1. **Run `01-install.bat`** — This creates the environment and opens `.env` in Notepad
2. **Fill in `.env`** — Add your `GROQ_API_KEY` (free at console.groq.com) and your credentials for Pinterest, Facebook, Instagram, or Twitter.
3. **Edit `config.yaml`** — Set your `seed_keywords` (topics to post about) and `categories`
4. **Run `02-validate.bat`** — Confirms everything is working
5. **Run `03-test-mode.bat`** — Watch it do one full cycle without limits
6. **Run `06-start-scheduler.bat`** — Start the daily scheduler

For a full walkthrough, see [BEGINNERS_GUIDE_EN.md](BEGINNERS_GUIDE_EN.md).

---

## Manual Setup (Advanced)

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
# Start the agent (daily scheduler for all platforms)
python -m src.main start

# Run once for Pinterest
python -m src.main run-now

# Run once for Facebook
python -m src.main fb-run-now

# Run once for Instagram
python -m src.main insta-run-now

# Run once for Twitter (X)
python -m src.main twitter-run-now

# Check account status
python -m src.main stats
```

## Configuration

- **`config.yaml`** — Niche keywords, posting schedule, AI settings, safety limits
- **`.env`** — API keys and Pinterest credentials (never commit this)

## Project Structure

```
src/
├── main.py              # CLI entry point (Typer + Rich)
├── orchestrator.py      # Daily loop controller
├── models.py            # Shared data models
├── brain/               # Research & keyword discovery
├── creator/             # AI image + metadata generation
├── worker/              # Pinterest posting + safety
├── analyzer/            # Performance tracking + learning
├── store/               # SQLite database
├── diagnostic/          # AI-powered scraper self-healing
├── report/              # Cycle reports (rich CLI + file)
└── utils/               # Config, logging, constants
```

## Docs

- [BEGINNERS_GUIDE_EN.md](BEGINNERS_GUIDE_EN.md) — Step-by-step walkthrough for new users
- [BEGINNERS_GUIDE_AR.md](BEGINNERS_GUIDE_AR.md) — دليل المبتدئين باللغة العربية
- [BEGINNERS_GUIDE_FR.md](BEGINNERS_GUIDE_FR.md) — Guide du débutant en français
- [PRD](prd.md) — What this project does and why
- [Spec](spec.md) — Technical specification and architecture
- [AGENTS.md](AGENTS.md) — Rules for AI agents building this project
