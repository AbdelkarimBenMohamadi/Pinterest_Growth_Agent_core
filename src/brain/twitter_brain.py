import asyncio
import logging
import random
from playwright.async_api import async_playwright, Page
from src.models import Keyword
from src.store.database import Database

logger = logging.getLogger(__name__)

async def discover_twitter_trends(seed_keywords: list[str], db: Database, config: dict, twitter_client=None) -> list[Keyword]:
    """
    Discover trending topics on Twitter.
    Uses an authenticated browser session if twitter_client is provided.
    """
    all_keywords: list[Keyword] = []

    try:
        page = await twitter_client._launch() if twitter_client else None
        if not page:
            logger.warning("No authenticated page provided for Twitter trend discovery.")
            return []

        # Navigate to Explore / Trends
        await page.goto("https://twitter.com/explore/tabs/trending", timeout=30000)
        await asyncio.sleep(5)

        # Extract trend names from the sidebar or main list
        extracted = await page.evaluate("""
            () => {
                const results = [];
                // Look for elements that usually contain trend titles
                const elements = document.querySelectorAll('[data-testid="trend"] div[dir="ltr"] span');
                for (const el of elements) {
                    const text = el.innerText.trim();
                    if (text && text.length > 2 && text.length < 50) {
                        results.push(text);
                    }
                }
                return results;
            }
        """)

        seen = set()
        for i, t in enumerate(extracted):
            t_clean = t.lower()
            if t_clean not in seen:
                seen.add(t_clean)
                kw = Keyword(
                    term=t,
                    suggestion_rank=i + 1,
                    related_terms=["twitter_trends"],
                    source="twitter_explore"
                )
                db.upsert_keyword(kw)
                all_keywords.append(kw)

    except Exception as e:
        logger.debug(f"Twitter trend extraction failed: {e}")

    return all_keywords[:15]
