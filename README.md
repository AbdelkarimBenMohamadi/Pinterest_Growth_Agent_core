# Pinterest Growth Agent (PGA)

An autonomous AI agent that grows your Pinterest account by finding high-demand keywords, generating optimized pins, and posting them safely — all on autopilot.

## How It Works

```text
Research → Generate → Post → Learn → Repeat (daily)
```

1. **Research** — Scrapes Pinterest for trending topics and high-value keywords
2. **Generate** — Creates unique AI images + SEO-optimized metadata
3. **Post** — Publishes pins safely via Playwright and verifies the real Pinterest URL
4. **Learn** — Tracks performance and prioritizes what works

---

## Quick Start with Batch Files (Beginners)

Double-click these files in order — no command line needed:

| File | What It Does |
| --- | --- |
| **`01-install.bat`** | One-click install — Python environment, dependencies, Playwright |
| **`02-validate.bat`** | Checks everything is ready before you run |
| **`03-test-mode.bat`** | First-time test — does one full cycle, bypasses safety limits |
| **`04-run-once.bat`** | Normal on-demand run — respects safety limits |
| **`05-status.bat`** | View recent stats and keyword performance |
| **`06-start-scheduler.bat`** | Start the daily scheduler — runs forever in background |
| **`07-run-headless.bat`** | Run one cycle without opening a browser window |
| **`08-run-gui.bat`** | Run one cycle with a visible browser window |

macOS and Linux users can run the matching `.sh` files, for example `./01-install.sh`, `./04-run-once.sh`, or `./07-run-headless.sh`.

### First Time Setup

1. **Run `01-install.bat`** — This creates the environment and opens `.env` in Notepad
2. **Fill in `.env`** — Add `PINTEREST_EMAIL`, `PINTEREST_PASSWORD`, `DEEPSEEK_API_KEY`, and `OPENAI_API_KEY`
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
# Start the agent (daily scheduler)
python -m src.main start

# Run once immediately (single on-demand cycle)
python -m src.main run-now --schedule-mode immediate

# Run exactly one pin for a safer smoke test
python -m src.main run-now --schedule-mode immediate --max-pins 1

# Run one cycle and wait for scheduled pin times
python -m src.main run-now --schedule-mode scheduled

# Override browser mode for this run
python -m src.main run-now --browser-mode headless --schedule-mode immediate

# Retry posting an existing generated pin without regenerating image or metadata
python -m src.main retry-post 2 --browser-mode gui
python -m src.main retry-post 2 --browser-mode headless

# Check account status
python -m src.main stats
```

## Configuration

- **`config.yaml`** — Niche keywords, posting schedule, AI settings, safety limits
- **`.env`** — API keys and Pinterest credentials (never commit this)

The current cost-optimized text default is DeepSeek:

```yaml
ai:
  text_provider: "deepseek"
  text_model: "deepseek-v4-flash"
  quality_gate_model: "deepseek-v4-flash"
  self_healing_model: "deepseek-v4-pro"
```

This requires `DEEPSEEK_API_KEY` in `.env`.

The current image default is OpenAI Images:

```yaml
ai:
  image_provider: "openai"
  openai_image_model: "gpt-image-1"
  openai_image_size: "1024x1536"
  openai_image_quality: "medium"
```

This requires `OPENAI_API_KEY` in `.env`. If OpenAI image generation fails, the agent falls back to Pollinations, then the existing Together/Hugging Face fallbacks when configured.

Browser mode is controlled with:

```yaml
browser:
  mode: gui # gui | headless
```

Posting can either wait for computed peak-hour times or post immediately:

```yaml
posting:
  schedule_mode: scheduled # scheduled | immediate
```

For safer live testing:

```bash
# Generate and try at most one pin
python -m src.main run-now --force --schedule-mode immediate --max-pins 1

# Retry a pin already saved in the local database
python -m src.main retry-post <pin_id> --browser-mode gui
```

`retry-post` is the safest way to test posting fixes because it reuses an existing image and metadata. It does not call the image generator again.

## Posting Verification

PGA no longer treats an unknown Pinterest result as a successful post. A pin is marked `posted` only after the tool verifies a real Pinterest URL like:

```text
https://www.pinterest.com/pin/<id>/
```

Possible posting statuses:

| Status | Meaning |
| --- | --- |
| `posted` | Pinterest accepted the pin and PGA verified a real `/pin/<id>/` URL |
| `unverified` | The publish flow may have advanced, but no verified pin URL was found |
| `failed` | A required step failed, such as board selection or publish button readiness |

For `unverified` or `failed` posts, PGA writes debug artifacts under `data/post_debug/`, including screenshots, the page HTML, and relevant network logs. Cycle reports are written to `data/cycle_report.log` and timestamped files in `data/cycle_reports/`.

## Browser And Account Support

- GUI mode opens one Chromium window and reuses it for login, research, posting, and verification.
- Headless mode runs without showing a browser window.
- Safe scraper mode reuses the existing browser page in GUI mode.
- Fast scraper mode is for advanced/headless use because it can open separate browser contexts.
- PGA detects Pinterest account type as `personal`, `business`, or `unknown` and includes it in each report.
- Business-account board selectors and publish behavior are supported.

## Project Structure

```markdown
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
