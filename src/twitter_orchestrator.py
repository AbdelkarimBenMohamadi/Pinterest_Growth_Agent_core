import asyncio
import logging
from datetime import datetime

from src.store.database import Database
from src.brain.twitter_brain import discover_twitter_trends
from src.brain.decision_engine import select_todays_content
from src.creator.image_generator import generate_image
from src.creator.metadata_generator import generate_metadata
from src.worker.twitter_client import TwitterClient
from src.worker.scheduler import distribute_posting_times, get_daily_limits
from src.worker.safety_manager import SafetyManager
from src.models import TwitterPost

logger = logging.getLogger(__name__)

async def run_twitter_daily_cycle(db: Database, config: dict, force: bool = False) -> None:
    """
    The complete daily agent cycle for Twitter:
    1. Check credentials
    2. Check safety limits
    3. Research (trends)
    4. Decide content mix
    5. Generate images + metadata
    6. Post to Twitter
    """
    import os
    if not os.getenv("TWITTER_USERNAME") or not os.getenv("TWITTER_PASSWORD"):
        logger.info("Twitter credentials not set. Skipping Twitter cycle.")
        return

    logger.info("=== Starting Twitter daily cycle ===")

    safety = SafetyManager(db, config, platform='twitter')
    if safety.is_in_cooldown():
        logger.warning("Twitter account in cooldown. Skipping cycle.")
        return

    niche = config.get("niche", {})
    seed_keywords = niche.get("seed_keywords", [])

    twitter_client = TwitterClient(config, db=db)

    try:
        logged_in = await twitter_client.login()
        if not logged_in:
            logger.error("Twitter login failed. Skipping cycle.")
            return

        logger.info("Step 1: Twitter Research")
        keywords = await discover_twitter_trends(seed_keywords, db, config, twitter_client=twitter_client)
        logger.info(f"Found {len(keywords)} Twitter trends")

        logger.info("Step 2: Decision")
        created_date_str = config.get("account", {}).get("created_date", "2026-04-24")
        created_date = datetime.strptime(created_date_str, "%Y-%m-%d")
        limits = get_daily_limits(created_date)

        briefs = select_todays_content(keywords, [], limits.max_pins, 100)

        if not briefs:
            logger.warning("No content briefs generated for Twitter. Skipping cycle.")
            return

        logger.info(f"Step 3: Generate and Post ({len(briefs)} tweets)")

        for i, brief in enumerate(briefs):
            if not safety.check_daily_limits() and not force:
                logger.warning("Daily limits reached. Skipping remaining Twitter cycle.")
                break

            if not safety.check_hourly_limits():
                logger.warning("Hourly limits reached. Waiting...")
                await asyncio.sleep(60)
                continue

            try:
                logger.info(f"Processing Twitter brief {i+1}/{len(briefs)}: {brief.target_keyword}")

                image_path, image_hash = await generate_image(brief, config)
                metadata = await generate_metadata(brief, config)

                tweet_text = f"{metadata.title}\n\n{metadata.description}"
                if metadata.hashtags:
                    tweet_text += "\n\n" + " ".join([f"#{h.replace(' ', '')}" for h in metadata.hashtags[:3]])

                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."

                post = TwitterPost(
                    image_path=image_path,
                    image_hash=image_hash,
                    tweet_text=tweet_text,
                    target_keyword=brief.target_keyword,
                    content_type=brief.content_type,
                    status="pending"
                )
                post_id = db.insert_twitter_post(post)

                success = await twitter_client.post_tweet(tweet_text, image_path)

                if success:
                    logger.info(f"Successfully posted tweet: {brief.target_keyword}")
                    db.update_twitter_post_status(post_id, "posted")
                    db.log_action("twitter_post", {"keyword": brief.target_keyword, "status": "success", "post_id": post_id}, platform='twitter')
                else:
                    logger.warning(f"Failed to post tweet: {brief.target_keyword}")
                    db.update_twitter_post_status(post_id, "failed")

                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error processing Twitter brief '{brief.target_keyword}': {e}")
                continue

    finally:
        await twitter_client.close()

    logger.info("=== Twitter daily cycle complete ===")
