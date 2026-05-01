# Beginner's Guide to Pinterest Growth Agent

> **Welcome!** This guide walks you through every step from downloading the project to your first successful pin post. No technical knowledge required.

---

## What Is This Tool?

Pinterest Growth Agent (PGA) is an AI-powered bot that automatically:
- Finds what people are searching for on Pinterest
- Creates beautiful pin images using AI
- Writes SEO-optimized titles and descriptions
- Posts pins to your Pinterest account on a schedule
- Learns which keywords perform best and does more of what works

Think of it as having a 24/7 Pinterest assistant that never sleeps.

---

## Before You Start

### What You'll Need

| Requirement | What It Is | Where to Get It |
|---|---|---|
| Python 3.11+ | The programming language the tool runs on | [python.org](https://www.python.org/downloads/) |
| A Pinterest account | Your Pinterest profile | [pinterest.com](https://www.pinterest.com) |
| A Groq API key | Free AI key for generating text | [console.groq.com](https://console.groq.com) (free, no credit card) |

### Supported Operating Systems

- **Windows 10/11** — Full support, all batch files work as-is
- **macOS / Linux** — Use the manual commands in the README instead of batch files

---

## Step-by-Step Installation

### Step 1: Download the Project

Download the project folder to your computer and extract it if it came as a ZIP file. Keep the folder in an easy-to-find location like your Desktop.

### Step 2: Run the Setup Wizard

Double-click **`01-install.bat`**

This will automatically:
- Create a Python virtual environment (keeps things organized)
- Install all required Python packages
- Install the Chromium browser (used for Pinterest automation)
- Create a `.env` file and open it in Notepad for you to fill in

The setup window will tell you when it's complete. It takes about 3-5 minutes on a fast connection.

### Step 3: Get Your Free Groq API Key

1. Open [console.groq.com](https://console.groq.com) in your browser
2. Sign up for a free account (or log in)
3. Click **"API Keys"** in the sidebar
4. Click **"Create API Key"**
5. Give it any name (e.g., "Pinterest Agent")
6. Copy the key — it looks like `gsk_xxxxxxxxxxxxxxxxxxxxxx`

### Step 4: Fill In Your `.env` File

The setup wizard opened Notepad with your `.env` file. It should look like this:

```env
# Pinterest Login Credentials (required if session state doesn't exist)
PINTEREST_EMAIL=your_pinterest_email@example.com
PINTEREST_PASSWORD=your_pinterest_password

# Groq API (free at console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxx

# Image generation fallback (optional — leave blank for now)
TOGETHER_API_KEY=
HF_API_KEY=
```

Fill in:
- `PINTEREST_EMAIL` — the email you use to log into Pinterest
- `PINTEREST_PASSWORD` — your Pinterest password
- `GROQ_API_KEY` — paste your key from Step 3

**Important:** You can leave `TOGETHER_API_KEY` and `HF_API_KEY` blank. These are backup image providers and are not required.

Save the file and close Notepad.

### Step 5: Configure Your Niche

Open `config.yaml` in any text editor (double-click it). This tells the agent what topics to post about.

Find the `niche` section and replace the example keywords with your own:

```yaml
# Example for Islamic content:
niche:
  seed_keywords:
    - "Islamic Reminders"
    - "Morning Azkar"
    - "Tawheed Allah"
    - "Istighfar Benefits"
  categories:
    - "Islam"
    - "Islamic Reminders"

# Example for Home Decor:
niche:
  seed_keywords:
    - "Modern living room ideas"
    - "Minimalist home decor"
    - "Cozy bedroom design"
  categories:
    - "Home Decor"
    - "Interior Design"
```

**Choose topics you actually want to post about.** The agent will find related search terms automatically.

### Step 6: Validate Everything

Double-click **`02-validate.bat`**

This checks:
- Python is installed correctly
- All packages are installed
- Your Chromium browser is ready
- Your `.env` file has all the required keys

If any check fails, the tool will tell you exactly what's wrong and how to fix it.

### Step 7: Run Your First Cycle

Double-click **`03-test-mode.bat`**

> Use this instead of `04-run-once.bat` for your first test — it bypasses safety limits so you can see the full posting process without worrying about daily caps.

This runs one complete cycle immediately so you can see what happens:
1. **Research** — Scrapes Pinterest for keywords and trends
2. **Generate** — Creates AI images and metadata
3. **Post** — Publishes pins to your Pinterest account
4. **Analyze** — Checks how your pins performed

You'll see colored output in the window as each step completes. A detailed report appears at the end showing:
- How many keywords were found
- How many pins were posted
- Any errors or warnings

This first run may take 5-10 minutes since it has to generate images and log into Pinterest.

**After your first test**, use `04-run-once.bat` for normal on-demand runs — it respects safety limits.

---

## Understanding the Batch Files

| File | When to Use It |
|---|---|
| **`01-install.bat`** | Run once when you first download the project |
| **`02-validate.bat`** | Run before each session to make sure everything is working |
| **`04-run-once.bat`** | Normal on-demand cycle — respects safety limits |
| **`03-test-mode.bat`** | **Full force test** — bypasses limits for testing and debugging |
| **`06-start-scheduler.bat`** | Start the daily scheduler (runs in background, use this for continuous posting) |
| **`05-status.bat`** | Check your stats — keywords, pins posted, engagement |

---

## How the Daily Schedule Works

When you run `06-start-scheduler.bat`, the agent starts a background scheduler that runs once per day at the hour specified in `config.yaml`.

**Default schedule** (in `config.yaml`):
```yaml
schedule:
  start_hour: 8        # Runs at 8:00 AM (your local time, see timezone below)
  peak_hours: [10, 14, 18, 20]  # Pin posting distributed across these hours
  timezone: "US/Eastern"
```

**Account Safety Limits** — The agent limits how many pins it posts based on account age to avoid bans:

| Account Age | Max Pins/Day | Max Total Actions |
|---|---|---|
| Days 1-7 | 1 pin | 10 |
| Days 8-14 | 2 pins | 20 |
| Days 15-30 | 5 pins | 40 |
| 31+ days | 8 pins | 60 |

These limits are applied automatically based on the `account.created_date` you set in `config.yaml`.

---

## Understanding the Output

### What the Colors Mean

- **Green** — Success
- **Yellow/Orange** — Warning (something unexpected but the agent handled it)
- **Red** — Error (the agent will try to recover or skip)
- **Cyan/Magenta** — Information / research data

### Key Terms

| Term | Meaning |
|---|---|
| **Keyword** | A search term the agent found on Pinterest |
| **Content Brief** | A plan for one pin (keyword + content type) |
| **Board** | A Pinterest board (like a folder) where pins are saved |
| **Engagement** | How people interact with your pins — saves, clicks |
| **CTR** | Click-Through Rate — % of people who clicked your pin |
| **Save Rate** | % of people who saved your pin to their board |
| **Cooldown** | Safety mode — the agent stops posting temporarily |
| **Shadowban** | When Pinterest hides your pins from search |

---

## Troubleshooting

### "Python not found" during setup
- Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation
- Restart your computer after installing Python

### "GROQ_API_KEY not set" error
- Open `.env` in Notepad
- Make sure you pasted your key correctly (no extra spaces)
- The key should start with `gsk_`

### Pin posted but I can't see it on Pinterest
- Wait 5 minutes — Pinterest can be slow to update
- Try refreshing your Pinterest profile
- Check if the pin was saved to a different board than expected
- Run `05-status.bat` to see the logged URL

### Agent stopped or crashed
- Check the error message at the bottom of the window
- Most errors are temporary (internet hiccup, Pinterest is busy)
- Just run `04-run-once.bat` again to continue

### "Session not valid" / Login failed
- Delete `data/pinterest_session.json` and run again
- Make sure your Pinterest email and password are correct in `.env`
- Pinterest may require email verification on first login from a new device

### Too many failures in validate.bat
- Make sure you ran `01-install.bat` successfully
- Try running `01-install.bat` again
- Check that your internet connection is working

---

## Frequently Asked Questions

**Q: Will this get my Pinterest account banned?**
A: The agent is designed with safety limits and uses browser automation that mimics real user behavior. It will never post more pins than your account age allows. It also detects shadowbans and enters cooldown mode automatically.

**Q: How many pins will it post per day?**
A: Based on the warming schedule, between 1-8 pins per day depending on how old your account is. Older accounts can post more.

**Q: Do I need to keep my computer on?**
A: Yes — the agent runs on your computer. If you close the window, the scheduler stops. For 24/7 operation, consider running on a always-on device like a Raspberry Pi or a cloud VPS.

**Q: Can I use my own ComfyUI for image generation?**
A: Yes! Set `comfyui.enabled: true` in `config.yaml` and fill in the `host`, `port`, and `model` settings. ComfyUI must be running locally for this to work.

**Q: Can I change the posting schedule?**
A: Yes — edit `config.yaml`. Change `peak_hours` to the hours you want pins posted, and `timezone` to your local timezone.

**Q: What is the difference between 04-run-once.bat and 03-test-mode.bat?**
A: `04-run-once.bat` respects safety limits — use it for normal daily use. `03-test-mode.bat` bypasses limits — use it only for testing when setting up or debugging. Never use the force mode repeatedly on a live Pinterest account.

**Q: My first test posted 0 pins. Why?**
A: You may have hit a daily limit. Check the cycle report — it shows why pins weren't posted. New accounts (days 1-7) can only post 1 pin per day. Use `03-test-mode.bat` if you need to test the full posting flow without limits.

**Q: What happens if a keyword is repeated?**
A: The agent tracks which keywords have been used and prioritizes fresh keywords. Duplicate images are detected by hash and regenerated automatically.

---

## Files and Folders

```
pinterest-growth-agent/
├── 01-install.bat           ← Run this FIRST
├── 02-validate.bat         ← Check setup before running
├── 03-test-mode.bat         ← First time test (bypasses limits)
├── 04-run-once.bat         ← Normal on-demand cycle
├── 05-status.bat           ← View stats
├── 06-start-scheduler.bat  ← Start daily scheduler
├── config.yaml             ← Your settings (edit this!)
├── .env                    ← Your API keys (created by setup)
├── .env.example            ← Template for .env
├── data/                   ← Database and session files (auto-created)
├── assets/                 ← Generated images (auto-created)
├── src/                    ← The actual agent code (don't edit)
├── BEGINNERS_GUIDE.md      ← You are here!
└── README.md               ← Technical documentation
```

---

## Getting Help

If something isn't working:

1. **Run `02-validate.bat`** first — it catches most setup issues
2. Check the **Troubleshooting** section above
3. Look at the detailed report in `data/cycle_report.log` after a run
4. Search for your error message online — it's likely a known issue with a fix

---

*Happy Pinning!*