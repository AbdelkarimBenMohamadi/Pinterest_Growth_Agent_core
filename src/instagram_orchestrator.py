import asyncio
import logging
import random
from datetime import datetime

from src.store.database import Database
from src.brain.instagram_brain import discover_instagram_keywords
from src.brain.decision_engine import select_todays_content
from src.creator.image_generator import generate_image
from src.creator.metadata_generator import generate_metadata
from src.worker.instagram_client import InstagramClient
from src.worker.scheduler import distribute_posting_times, get_daily_limits
from src.worker.safety_manager import SafetyManager
from src.models import InstagramPost

logger = logging.getLogger(__name__)

async def run_instagram_daily_cycle(db: Database, config: dict, force: bool = False) -> None:
    """
    The complete daily agent cycle for Instagram:
    1. Check credentials
    2. Check safety limits
    3. Research (hashtags)
    4. Decide content mix
    5. Generate images + metadata
    6. Post to Instagram
    """
    from src.utils.config import has_instagram_credentials
    if not has_instagram_credentials():
        logger.info("Instagram credentials not set. Skipping Instagram cycle.")
        return

    logger.info("=== Starting Instagram daily cycle ===")

    safety = SafetyManager(db, config, platform='instagram')
    if safety.is_in_cooldown():
        logger.warning("Instagram account in cooldown. Skipping cycle.")
        return

    niche = config.get("niche", {})
    seed_keywords = niche.get("seed_keywords", [])

    insta_client = InstagramClient(config, db=db)

    try:
        logged_in = await insta_client.login()
        if not logged_in:
            logger.error("Instagram login failed. Skipping cycle.")
            return

        logger.info("Step 1: Instagram Research")
        keywords = await discover_instagram_keywords(seed_keywords, db, config, insta_client=insta_client)
        logger.info(f"Found {len(keywords)} Instagram-relevant keywords/hashtags")

        logger.info("Step 2: Decision")
        created_date_str = config.get("account", {}).get("created_date", "2026-04-24")
        created_date = datetime.strptime(created_date_str, "%Y-%m-%d")
        limits = get_daily_limits(created_date)

        # Instagram limits are usually stricter
        max_posts = min(limits.max_pins, 5)
        briefs = select_todays_content(keywords, [], max_posts, 100)

        if not briefs:
            logger.warning("No content briefs generated for Instagram. Skipping cycle.")
            return

        logger.info(f"Step 3: Generate and Post ({len(briefs)} posts)")

        for i, brief in enumerate(briefs):
            if not safety.check_daily_limits() and not force:
                logger.warning("Daily limits reached. Stopping Instagram cycle.")
                break

            if not safety.check_hourly_limits():
                logger.warning("Hourly limits reached. Waiting...")
                await asyncio.sleep(60)
                continue

            try:
                logger.info(f"Processing Instagram brief {i+1}/{len(briefs)}: {brief.target_keyword}")

                image_path, image_hash = await generate_image(brief, config)
                metadata = await generate_metadata(brief, config)

                caption = f"{metadata.title}\n\n{metadata.description}"
                if metadata.hashtags:
                    caption += "\n\n" + " ".join([f"#{h.replace(' ', '')}" for h in metadata.hashtags])

                post = InstagramPost(
                    image_path=image_path,
                    image_hash=image_hash,
                    caption=caption,
                    target_keyword=brief.target_keyword,
                    content_type=brief.content_type,
                    status="pending"
                )
                post_id = db.insert_instagram_post(post)

                success = await insta_client.post_content(image_path, caption)

                if success:
                    logger.info(f"Successfully posted to Instagram: {brief.target_keyword}")
                    db.update_instagram_post_status(post_id, "posted")
                    db.log_action("instagram_post", {"keyword": brief.target_keyword, "status": "success", "post_id": post_id}, platform='instagram')
                else:
                    logger.warning(f"Failed to post to Instagram: {brief.target_keyword}")
                    db.update_instagram_post_status(post_id, "failed")

                # Wait between posts (longer for Instagram)
                await asyncio.sleep(random.uniform(300, 600))

            except Exception as e:
                logger.error(f"Error processing Instagram brief '{brief.target_keyword}': {e}")
                continue

    finally:
        await insta_client.close()

    logger.info("=== Instagram daily cycle complete ===")
