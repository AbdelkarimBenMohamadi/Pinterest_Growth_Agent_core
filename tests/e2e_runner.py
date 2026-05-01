"""
End-to-End Test — Pinterest Growth Agent
Tests each module in order like a real user would experience it.
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Setup
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
logger = logging.getLogger("E2E_TEST")

RESULTS = {}

def report(step: str, status: bool, detail: str = ""):
    icon = "✅" if status else "❌"
    RESULTS[step] = status
    logger.info(f"{icon} {step}: {detail}")


async def test_step1_foundation():
    """Test config, logger, models, database."""
    logger.info("\n{'='*60}\n  STEP 1: Foundation\n{'='*60}")

    # Config
    try:
        from src.utils.config import load_config, get_groq_api_key, get_pinterest_credentials
        config = load_config()
        report("Config load", True, f"Keys: {list(config.keys())}")

        key = get_groq_api_key()
        report("Groq API key", bool(key), f"{'***' + key[-4:] if key else 'MISSING'}")

        email, pw = get_pinterest_credentials()
        report("Pinterest creds", bool(email and pw), f"Email: {email}")
    except Exception as e:
        report("Config", False, str(e))
        return None

    # Logger
    try:
        from src.utils.logger import setup_logging
        setup_logging()
        report("Logger", True, "Rich handler configured")
    except Exception as e:
        report("Logger", False, str(e))

    # Models
    try:
        from src.models import Keyword, Trend, ContentBrief, PinMetadata, Pin, EngagementData, DailyLimits
        kw = Keyword(term="test", suggestion_rank=1)
        report("Models", True, f"All 7 dataclasses importable")
    except Exception as e:
        report("Models", False, str(e))

    # Database
    try:
        from src.store.database import Database
        db = Database("data/test_e2e.db")
        db.initialize()
        
        # Test keyword roundtrip
        kw = Keyword(term="e2e test keyword", suggestion_rank=1, related_terms=["test"])
        db.upsert_keyword(kw)
        keywords = db.get_top_keywords(limit=5)
        assert any(k.term == "e2e test keyword" for k in keywords)
        report("Database", True, f"Init + keyword roundtrip OK ({len(keywords)} keywords)")
    except Exception as e:
        report("Database", False, str(e))
        return None

    return config


async def test_step2_brain(config: dict):
    """Test SEO scraper, trend monitor, decision engine."""
    logger.info(f"\n{'='*60}\n  STEP 2: Brain Module\n{'='*60}")

    from src.store.database import Database
    db = Database("data/test_e2e.db")
    db.initialize()

    # Decision engine (pure logic, no I/O — always works)
    try:
        from src.brain.decision_engine import select_todays_content
        from src.models import Keyword, Trend
        keywords = [Keyword(term=f"kw{i}", suggestion_rank=i, performance_score=float(10-i)) for i in range(10)]
        trends = [Trend(name=f"trend{i}", velocity=1.5) for i in range(5)]
        briefs = select_todays_content(keywords, trends, daily_pin_limit=10, seo_percent=70)
        seo = sum(1 for b in briefs if b.content_type == "seo")
        trend = sum(1 for b in briefs if b.content_type == "trend")
        report("Decision engine", seo == 7 and trend == 3, f"SEO={seo}, Trend={trend}")
    except Exception as e:
        report("Decision engine", False, str(e))

    # SEO scraper (needs network)
    try:
        from src.brain.seo_scraper import scrape_keywords
        seed = config.get("niche", {}).get("seed_keywords", ["home decor ideas"])[:1]
        keywords = await scrape_keywords(seed, db, config)
        report("SEO scraper", len(keywords) > 0, f"Found {len(keywords)} keywords for '{seed[0]}'")
    except Exception as e:
        report("SEO scraper", False, str(e))

    # Trend monitor (needs network)
    try:
        from src.brain.trend_monitor import fetch_trends
        cats = config.get("niche", {}).get("categories", ["Home Decor"])[:1]
        trends = await fetch_trends(cats, db, config)
        report("Trend monitor", len(trends) >= 0, f"Found {len(trends)} trends for '{cats[0]}'")
    except Exception as e:
        report("Trend monitor", False, str(e))


async def test_step3_creator(config: dict):
    """Test image generation, metadata generation, quality gate."""
    logger.info(f"\n{'='*60}\n  STEP 3: Creator Module\n{'='*60}")

    from src.models import ContentBrief

    brief = ContentBrief(
        target_keyword="minimalist kitchen design",
        content_type="seo",
        related_terms=["modern kitchen", "clean kitchen"],
        board_name="Kitchen Ideas"
    )

    # Image generation (Pollinations.ai)
    image_path = ""
    try:
        from src.creator.image_generator import generate_image
        image_path, image_hash = await generate_image(brief, config)
        file_exists = Path(image_path).exists()
        file_size = Path(image_path).stat().st_size if file_exists else 0
        report("Image generation", file_exists and file_size > 1000, 
               f"Path: {image_path}, Size: {file_size:,} bytes, Hash: {image_hash[:12]}...")
    except Exception as e:
        report("Image generation", False, str(e))

    # Metadata generation (Groq API)
    metadata = None
    try:
        from src.creator.metadata_generator import generate_metadata
        metadata = await generate_metadata(brief, config)
        report("Metadata generation", bool(metadata.title and metadata.description),
               f"Title: {metadata.title[:60]}...")
    except Exception as e:
        report("Metadata generation", False, str(e))

    # Quality gate
    try:
        from src.creator.quality_gate import check_alignment
        if metadata:
            aligned = await check_alignment(brief, metadata, "minimalist kitchen, clean design")
            report("Quality gate", True, f"Aligned: {aligned}")
        else:
            report("Quality gate", False, "Skipped — no metadata")
    except Exception as e:
        report("Quality gate", False, str(e))

    return image_path, metadata


async def test_step4_worker(config: dict, image_path: str, metadata):
    """Test Pinterest login and posting."""
    logger.info(f"\n{'='*60}\n  STEP 4: Worker Module\n{'='*60}")

    # Scheduler (pure logic)
    try:
        from src.worker.scheduler import get_daily_limits, distribute_posting_times
        from datetime import datetime
        limits = get_daily_limits(datetime(2026, 4, 1))  # ~24 days old
        report("Scheduler limits", limits.max_pins > 0, 
               f"max_pins={limits.max_pins}, max_actions={limits.max_actions}")

        times = distribute_posting_times(3, [10, 14, 18], "US/Eastern")
        report("Scheduler times", len(times) == 3, f"Times: {[t.strftime('%H:%M') for t in times]}")
    except Exception as e:
        report("Scheduler", False, str(e))

    # Safety manager
    try:
        from src.worker.safety_manager import SafetyManager
        from src.store.database import Database
        db = Database("data/test_e2e.db")
        safety = SafetyManager(db, config)
        can_post = safety.check_daily_limits()
        report("Safety manager", True, f"Can post: {can_post}, In cooldown: {safety.is_in_cooldown()}")
    except Exception as e:
        report("Safety manager", False, str(e))

    # Pinterest login
    try:
        from src.worker.pinterest_client import PinterestClient
        client = PinterestClient(config)
        logged_in = await client.login()
        report("Pinterest login", logged_in, "Session established" if logged_in else "Login failed")

        # We won't actually post — just verify the flow works up to login
        if logged_in:
            report("Pinterest ready", True, "Client logged in, ready to post pins")
        
        await client.close()
    except Exception as e:
        report("Pinterest login", False, str(e))


async def main():
    logger.info("""
╔══════════════════════════════════════════════════╗
║   Pinterest Growth Agent — End-to-End Test       ║
║   Testing all modules like a real user           ║
╚══════════════════════════════════════════════════╝
    """)

    # Step 1: Foundation
    config = await test_step1_foundation()
    if not config:
        logger.error("Foundation failed. Cannot continue.")
        return

    # Step 2: Brain
    await test_step2_brain(config)

    # Step 3: Creator
    image_path, metadata = await test_step3_creator(config)

    # Step 4: Worker
    await test_step4_worker(config, image_path, metadata)

    # Final Report
    logger.info(f"\n{'='*60}")
    logger.info("  FINAL REPORT")
    logger.info(f"{'='*60}")
    passed = sum(1 for v in RESULTS.values() if v)
    failed = sum(1 for v in RESULTS.values() if not v)
    total = len(RESULTS)

    for step, status in RESULTS.items():
        icon = "✅" if status else "❌"
        logger.info(f"  {icon} {step}")

    logger.info(f"\n  Results: {passed}/{total} passed, {failed} failed")
    
    # Cleanup test DB
    try:
        Path("data/test_e2e.db").unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
