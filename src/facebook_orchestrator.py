import asyncio
import logging
from datetime import datetime, timezone as tz

from src.store.database import Database
from src.brain.facebook_brain import discover_facebook_keywords
from src.brain.decision_engine import select_todays_content
from src.creator.image_generator import generate_image
from src.creator.metadata_generator import generate_metadata
from src.worker.facebook_client import FacebookClient
from src.worker.scheduler import distribute_posting_times, get_daily_limits
from src.worker.safety_manager import SafetyManager
from src.models import FacebookPost

logger = logging.getLogger(__name__)

async def run_facebook_daily_cycle(db: Database, config: dict, force: bool = False) -> None:
    """
    The complete daily agent cycle for Facebook:
    1. Check credentials
    2. Check safety limits
    3. Research (keywords relevant to Facebook)
    4. Decide content mix
    5. Generate images + metadata
    6. Post to Facebook
    """
    from src.utils.config import has_facebook_credentials
    if not has_facebook_credentials():
        logger.info("Facebook credentials not set. Skipping Facebook cycle.")
        return

    logger.info("=== Starting Facebook daily cycle ===")

    safety = SafetyManager(db, config, platform='facebook')
    if safety.is_in_cooldown():
        logger.warning("Facebook account in cooldown. Skipping cycle.")
        return

    niche = config.get("niche", {})
    seed_keywords = niche.get("seed_keywords", [])

    fb_client = FacebookClient(config, db=db)

    try:
        logged_in = await fb_client.login()
        if not logged_in:
            logger.error("Facebook login failed. Skipping cycle.")
            return

        logger.info("Step 1: Facebook Research")
        keywords = await discover_facebook_keywords(seed_keywords, db, config, fb_client=fb_client)
        logger.info(f"Found {len(keywords)} Facebook-relevant keywords")

        logger.info("Step 2: Decision")
        created_date_str = config.get("account", {}).get("created_date", "2026-04-24")
        created_date = datetime.strptime(created_date_str, "%Y-%m-%d")
        limits = get_daily_limits(created_date)

        # Re-use content selection logic
        briefs = select_todays_content(keywords, [], limits.max_pins, 100) # 100% SEO for now

        if not briefs:
            logger.warning("No content briefs generated. Skipping cycle.")
            return

        logger.info(f"Step 3: Generate and Post ({len(briefs)} posts)")

        for i, brief in enumerate(briefs):
            if not safety.check_daily_limits() and not force:
                logger.warning("Daily limits reached. Stopping Facebook cycle.")
                break

            if not safety.check_hourly_limits():
                logger.warning("Hourly limits reached. Waiting...")
                await asyncio.sleep(60)
                continue

            try:
                logger.info(f"Processing brief {i+1}/{len(briefs)}: {brief.target_keyword}")

                # Generate image
                image_path, image_hash = await generate_image(brief, config)

                # Generate metadata (can reuse PinMetadata logic for text)
                metadata = await generate_metadata(brief, config)

                post_text = f"{metadata.title}\n\n{metadata.description}"
                if metadata.hashtags:
                    post_text += "\n\n" + " ".join(metadata.hashtags)

                post = FacebookPost(
                    image_path=image_path,
                    image_hash=image_hash,
                    text=post_text,
                    target_keyword=brief.target_keyword,
                    page_name=config.get("account", {}).get("facebook_page_id", ""),
                    content_type=brief.content_type,
                    status="pending"
                )
                post_id = db.insert_facebook_post(post)

                # Post to Facebook
                success = await fb_client.post_content(post_text, image_path)

                if success:
                    logger.info(f"Successfully posted to Facebook: {brief.target_keyword}")
                    db.update_facebook_post_status(post_id, "posted")
                    db.log_action("facebook_post", {"keyword": brief.target_keyword, "status": "success", "post_id": post_id}, platform='facebook')
                else:
                    logger.warning(f"Failed to post to Facebook: {brief.target_keyword}")
                    db.update_facebook_post_status(post_id, "failed")

                await asyncio.sleep(60) # Wait between posts

            except Exception as e:
                logger.error(f"Error processing Facebook brief '{brief.target_keyword}': {e}")
                continue

    finally:
        await fb_client.close()

    logger.info("=== Facebook daily cycle complete ===")
