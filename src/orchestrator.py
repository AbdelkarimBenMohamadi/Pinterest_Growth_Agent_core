import asyncio
import logging
import time
from datetime import datetime, timezone as tz
from apscheduler.schedulers.background import BackgroundScheduler

from src.store.database import Database
from src.utils.config import load_config, get_posting_config
from src.brain.seo_scraper import scrape_keywords
from src.brain.trend_monitor import fetch_trends
from src.brain.decision_engine import select_todays_content
from src.creator.image_generator import generate_image
from src.creator.metadata_generator import generate_metadata
from src.creator.quality_gate import check_alignment
from src.worker.pinterest_client import PinterestClient
from src.worker.scheduler import distribute_posting_times, get_daily_limits
from src.worker.safety_manager import SafetyManager
from src.analyzer.engagement_scraper import scrape_engagement
from src.analyzer.feedback import update_keyword_scores
from src.diagnostic.diagnostic import run_all_diagnostics
from src.models import Pin
from src.report.cycle_report import CycleReport

logger = logging.getLogger(__name__)


async def run_daily_cycle(db: Database, config: dict, force: bool = False) -> None:
    """
    The complete daily agent cycle:
    1. Check cooldown
    2. Research (keywords + trends) with health tracking
    3. Run diagnostics if scrapers are unhealthy
    4. Decide content mix
    5. Generate images + metadata
    6. Quality check
    7. Post pins across the day
    8. Shadowban detection (if enabled)
    9. Scrape engagement
    10. Update keyword scores
    """

    logger = logging.getLogger(__name__)
    logger.info("=== Starting daily cycle ===")

    cycle_start = datetime.now(tz.utc)
    report = CycleReport(cycle_start)

    # Pre-fill destination link info for the report
    try:
        posting_cfg = get_posting_config(config)
        report.destination_link_mode = posting_cfg.get("destination_link_mode", "none")
        report.destination_link = posting_cfg.get("default_destination_link", "")
    except Exception:
        pass

    safety = SafetyManager(db, config)

    if safety.is_in_cooldown():
        logger.warning("Account in cooldown. Skipping posting cycle.")
        db.log_action("cycle_skip", {"reason": "cooldown_active"})
        return

    niche = config.get("niche", {})
    seed_keywords = niche.get("seed_keywords", [])
    categories = niche.get("categories", [])

    # Use a SINGLE PinterestClient for the entire cycle — guaranteed cleanup in finally
    pinterest_client = PinterestClient(config, db=db)

    try:
        logged_in = await pinterest_client.login()
        if not logged_in:
            logger.error("Login failed. Skipping posting cycle.")
            return

        logger.info("Step 1: Research")

        keywords = []
        trends = []
        research_error = None

        try:
            keywords = await scrape_keywords(seed_keywords, db, config)
            success = len(keywords) > 0
            db.record_scrape_run("seo_scraper", success=success, result_count=len(keywords))
            if not success:
                logger.warning("SEO scraper returned 0 keywords despite no exception")
        except Exception as e:
            logger.warning(f"SEO scraper failed: {e}")
            db.record_scrape_run("seo_scraper", success=False, result_count=0, error=str(e))
            research_error = str(e)

        try:
            trends = await fetch_trends(categories, db, config)
            success = len(trends) > 0
            db.record_scrape_run("trend_monitor", success=success, result_count=len(trends))
            if not success:
                logger.warning("Trend monitor returned 0 trends despite no exception")
        except Exception as e:
            logger.warning(f"Trend monitor failed: {e}")
            db.record_scrape_run("trend_monitor", success=False, result_count=0, error=str(e))
            research_error = str(e) if not research_error else research_error

        logger.info(f"Research complete: {len(keywords)} keywords, {len(trends)} trends")

        report.keywords_found = len(keywords)
        report.trends_found = len(trends)
        report.new_keywords = [kw.term for kw in keywords if kw.performance_score == 0.0]
        top_kws = db.get_top_keywords(limit=20)
        report.top_keywords = [
            {"term": kw.term, "performance_score": kw.performance_score, "suggestion_rank": kw.suggestion_rank}
            for kw in top_kws
        ]
        report.research_details = {
            "keywords": [{"term": kw.term, "suggestion_rank": kw.suggestion_rank, "source": kw.source} for kw in keywords[:50]],
            "trends": [{"name": t.name, "velocity": t.velocity, "category": t.category} for t in trends[:20]],
        }

        # Step 2: Run diagnostics if research had problems
        if research_error or len(keywords) < 3 or len(trends) < 3:
            logger.info("Running diagnostic agent...")
            try:
                diag_results = await run_all_diagnostics(config, db)
                for result in diag_results:
                    logger.info(f"Diagnostic: {result['module']} — {result['diagnosis'].get('severity', 'unknown')}")
            except Exception as e:
                logger.warning(f"Diagnostic agent failed: {e}")

        logger.info("Step 3: Decision")

        created_date_str = config.get("account", {}).get("created_date", "2026-04-24")
        created_date = datetime.strptime(created_date_str, "%Y-%m-%d")
        limits = get_daily_limits(created_date)
        seo_percent = config.get("strategy", {}).get("seo_percent", 70)

        briefs = select_todays_content(keywords, trends, limits.max_pins, seo_percent)
        logger.info(f"Decision complete: {len(briefs)} content briefs to create")

        report.briefs_created = len(briefs)

        if not briefs:
            logger.warning("No content briefs generated. Skipping cycle.")
            db.log_action("cycle_skip", {"reason": "no_briefs"})
            return

        logger.info("Step 4: Generate and Post")
        peak_hours = config.get("schedule", {}).get("peak_hours", [10, 14, 18, 20])
        tz_name = config.get("schedule", {}).get("timezone", "US/Eastern")
        scheduled_times = distribute_posting_times(len(briefs), peak_hours, tz_name)

        # Track successfully posted pins for shadowban checking
        posted_pins: list[tuple[int, str]] = []  # (pin_id, pin_title)

        for i, brief in enumerate(briefs):
            if not safety.check_daily_limits() and not force:
                logger.warning("Daily limits reached. Stopping.")
                break

            if not safety.check_hourly_limits():
                logger.warning("Hourly limits reached. Waiting...")
                await asyncio.sleep(60)
                continue

            try:
                logger.info(f"Processing brief {i+1}/{len(briefs)}: {brief.target_keyword}")

                image_path, image_hash = await generate_image(brief, config)
                logger.info(f"Image generated: {image_path}")
                report.images_generated += 1

                if db.hash_exists(image_hash):
                    logger.warning(f"Duplicate image hash {image_hash}. Regenerating with new prompt...")
                    image_path, image_hash = await generate_image(brief, config, retry=True)

                if db.hash_exists(image_hash):
                    logger.warning(f"Still duplicate hash for '{brief.target_keyword}'. Skipping.")
                    db.log_action("duplicate_image", {"keyword": brief.target_keyword, "hash": image_hash})
                    continue

                metadata = await generate_metadata(brief, config)
                logger.info(f"Metadata generated: {metadata.title}")

                image_prompt = f"No people, no person, no woman, no female, no face, no humans. Pinterest pin style, {brief.target_keyword}, professional photography, 2:3 vertical, clean composition"
                aligned = await check_alignment(brief, metadata, image_prompt)

                if not aligned:
                    logger.warning(f"Quality gate failed for '{brief.target_keyword}'. Skipping.")
                    db.log_action("quality_gate_failed", {"keyword": brief.target_keyword})
                    continue

                scheduled_dt = scheduled_times[i] if i < len(scheduled_times) else None

                pin = Pin(
                    image_path=image_path,
                    image_hash=image_hash,
                    title=metadata.title,
                    description=metadata.description,
                    alt_text=metadata.alt_text,
                    target_keyword=brief.target_keyword,
                    board_name=metadata.suggested_board or brief.board_name,
                    content_type=brief.content_type,
                    status="pending",
                    scheduled_at=scheduled_dt,
                )
                pin_id = db.insert_pin(pin)
                logger.info(f"Pin {pin_id} created and queued for posting")

                board_name = metadata.suggested_board or brief.board_name or "PGA Pins"

                link_mode = metadata.destination_link_mode
                dest_link = metadata.default_destination_link if link_mode in ("destination_link", "both") else ""

                pin_url = await pinterest_client.post_pin(image_path, metadata, board_name, dest_link)

                if pin_url and pin_url != "":
                    if "/pin/" in pin_url and "pin-creation-tool" not in pin_url:
                        db.update_pin_posted(pin_id, "posted", pin_url, "post", {"pin_id": pin_id, "url": pin_url})
                        logger.info(f"Pin {pin_id} posted: {pin_url}")
                        posted_pins.append((pin_id, metadata.title))
                        report.pins_posted += 1
                        report.posted_pins.append({
                            "id": pin_id,
                            "keyword": brief.target_keyword,
                            "title": metadata.title,
                            "board": board_name,
                            "status": "posted",
                            "url": pin_url,
                        })
                    elif pin_url == "posted_unknown":
                        db.update_pin_posted(pin_id, "posted", None, "post_unknown", {"pin_id": pin_id, "note": "Pin likely posted but URL could not be determined"})
                        logger.warning(f"Pin {pin_id} posted (URL unknown)")
                        posted_pins.append((pin_id, metadata.title))
                        report.pins_posted += 1
                        report.posted_pins.append({
                            "id": pin_id,
                            "keyword": brief.target_keyword,
                            "title": metadata.title,
                            "board": board_name,
                            "status": "posted",
                            "url": "",
                        })
                    else:
                        db.update_pin_posted(pin_id, "failed", None, "post_failed", {"pin_id": pin_id, "url": pin_url})
                        logger.warning(f"Pin {pin_id} failed to post — unexpected URL: {pin_url}")
                        report.pins_failed += 1
                        report.errors.append(f"Pin {pin_id} failed with unexpected URL: {pin_url}")
                else:
                    db.update_pin_posted(pin_id, "failed", None, "post_failed", {"pin_id": pin_id})
                    logger.warning(f"Pin {pin_id} failed to post")
                    report.pins_failed += 1
                    report.errors.append(f"Pin {pin_id} failed to post (no URL returned)")

                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error processing brief '{brief.target_keyword}': {e}")
                db.log_action("error", {"keyword": brief.target_keyword, "error": str(e)})
                continue

        # Step 5: Shadowban detection (if enabled)
        enable_shadowban = config.get("safety", {}).get("enable_shadowban_check", False)
        if enable_shadowban and posted_pins:
            logger.info("Step 5: Shadowban detection")
            # Check visibility of the first posted pin as a canary
            canary_pin_id, canary_title = posted_pins[0]
            try:
                visible = await pinterest_client.check_pin_visibility(canary_title)
                if not visible:
                    logger.warning(f"Shadowban detected! Pin '{canary_title}' not visible in search.")
                    cooldown_hours = config.get("safety", {}).get("cooldown_hours", 48)
                    safety.enter_cooldown(cooldown_hours)
                    report.shadowban_detected = True
                    db.log_action("shadowban_detected", {
                        "pin_id": canary_pin_id,
                        "pin_title": canary_title,
                        "action": f"cooldown_{cooldown_hours}h"
                    })
                else:
                    logger.info(f"Shadowban check passed — pin '{canary_title}' is visible")
                    report.shadowban_check_passed = True
            except Exception as e:
                logger.warning(f"Shadowban check failed: {e}")

        # Step 6: Scrape engagement (reuse same client)
        logger.info("Step 6: Scrape engagement")
        try:
            recent_pins = db.get_recent_pins(days=7)
            if recent_pins:
                engagement_data = await scrape_engagement(pinterest_client, recent_pins, db)
                logger.info(f"Scraped engagement for {len(engagement_data)} pins")
                update_keyword_scores(engagement_data, db)
                logger.info("Keyword scores updated")
                report.engagement_summary = [
                    {
                        "pin_id": e.pin_id,
                        "keyword": next((p.target_keyword for p in recent_pins if p.id == e.pin_id), ""),
                        "saves": e.saves,
                        "clicks": e.clicks,
                        "ctr": e.ctr,
                        "save_rate": e.save_rate,
                    }
                    for e in engagement_data
                ]
            else:
                logger.info("No recent pins to scrape engagement for")
        except Exception as e:
            logger.error(f"Engagement scraping failed: {e}")
            report.errors.append(f"Engagement scraping failed: {e}")

    finally:
        report.finish()
        # Scraper health
        health = db.get_scraper_health()
        for h in health:
            if h["module_name"] == "seo_scraper":
                report.seo_scraper_health = h
            elif h["module_name"] == "trend_monitor":
                report.trend_scraper_health = h

        # Print report to CLI and write to file
        try:
            report.print_summary()
            report.print_file_report()
        except Exception as e:
            logger.warning(f"Failed to generate cycle report: {e}", exc_info=True)

        # Guaranteed cleanup — single client, always closed
        try:
            await pinterest_client.close()
        except Exception:
            pass

    logger.info("=== Daily cycle complete ===")


def start_scheduler(config: dict) -> None:
    """Start APScheduler with the daily cycle."""
    scheduler = BackgroundScheduler(timezone=config.get("schedule", {}).get("timezone", "UTC"))
    db = Database(config["paths"]["database"])
    db.initialize()

    start_hour = config.get("schedule", {}).get("start_hour", 8)
    scheduler.add_job(
        run_daily_cycle, 'cron', hour=start_hour, minute=0,
        args=[db, config],
        id='daily_cycle',
        name='Daily Pinterest Growth Cycle'
    )

    scheduler.start()
    logger.info(f"Scheduler started. Daily cycle runs at {start_hour:02d}:00.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()