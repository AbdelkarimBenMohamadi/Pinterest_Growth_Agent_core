import asyncio
import logging
import random
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from src.models import Keyword
from src.store.database import Database

logger = logging.getLogger(__name__)

async def discover_instagram_keywords(seed_keywords: list[str], db: Database, config: dict, insta_client=None) -> list[Keyword]:
    """
    Discover keywords/hashtags on Instagram.
    Uses an authenticated browser session if insta_client is provided.
    """
    all_keywords: list[Keyword] = []

    if insta_client:
        page = await insta_client._launch()
        for seed in seed_keywords:
            try:
                logger.info(f"Extracting Instagram hashtags (authenticated) for seed: {seed}")
                terms = await _extract_instagram_hashtags(page, seed)
                for rank, term in enumerate(terms):
                    kw = Keyword(term=term, suggestion_rank=rank + 1, related_terms=[seed], source="instagram_search")
                    db.upsert_keyword(kw)
                    all_keywords.append(kw)
                await asyncio.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.warning(f"Instagram authenticated discovery failed for '{seed}': {e}")
        return all_keywords

    stealth = Stealth()
    async with stealth.use_async(async_playwright()) as p:
        try:
            headless = config.get("browser", {}).get("headless", False)
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 375, "height": 812},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
            )
            page = await context.new_page()

            for seed in seed_keywords:
                try:
                    logger.info(f"Extracting Instagram hashtags for seed: {seed}")
                    terms = await _extract_instagram_hashtags(page, seed)

                    for rank, term in enumerate(terms):
                        kw = Keyword(
                            term=term,
                            suggestion_rank=rank + 1,
                            related_terms=[seed],
                            source="instagram_search"
                        )
                        db.upsert_keyword(kw)
                        all_keywords.append(kw)

                    await asyncio.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Instagram keyword discovery failed for '{seed}': {e}")

            await browser.close()
        except Exception as e:
            logger.error(f"Failed to launch browser for Instagram keyword discovery: {e}")

    return all_keywords

async def _extract_instagram_hashtags(page: Page, keyword: str) -> list[str]:
    """
    Search Instagram and extract related hashtags/keywords.
    """
    terms: list[str] = []

    try:
        # Search for the keyword
        search_url = f"https://www.instagram.com/explore/tags/{keyword.replace(' ', '')}/"
        await page.goto(search_url, timeout=30000)
        await asyncio.sleep(5)

        # Extract text from page (hashtags often appearing in related section or posts)
        extracted = await page.evaluate("""
            () => {
                const results = [];
                // Look for links that start with /explore/tags/
                const links = document.querySelectorAll('a[href^="/explore/tags/"]');
                for (const link of links) {
                    const text = link.innerText.trim();
                    if (text && text.startsWith('#')) {
                        results.push(text.substring(1));
                    }
                }
                return results;
            }
        """)

        seen = set()
        for t in extracted:
            t_clean = t.lower()
            if t_clean not in seen and len(t_clean) > 2:
                seen.add(t_clean)
                terms.append(t)

    except Exception as e:
        logger.debug(f"Instagram hashtag extraction failed for '{keyword}': {e}")

    return terms[:10]
