import asyncio
import logging
import random
import re
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth
from src.models import Keyword
from src.store.database import Database

logger = logging.getLogger(__name__)

async def discover_facebook_keywords(seed_keywords: list[str], db: Database, config: dict, fb_client=None) -> list[Keyword]:
    """
    Discover keywords on Facebook by searching for seed keywords and
    extracting relevant terms from search results (pages, groups, posts).
    Uses an authenticated browser session if fb_client is provided.
    """
    all_keywords: list[Keyword] = []

    if fb_client:
        page = await fb_client._launch()
        for seed in seed_keywords:
            try:
                logger.info(f"Extracting Facebook terms (authenticated) for seed: {seed}")
                terms = await _extract_facebook_terms_with_page(page, seed)
                for rank, term in enumerate(terms):
                    kw = Keyword(term=term, suggestion_rank=rank + 1, related_terms=[seed], source="facebook_search")
                    db.upsert_keyword(kw)
                    all_keywords.append(kw)
                await asyncio.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.warning(f"Facebook authenticated discovery failed for '{seed}': {e}")
        return all_keywords

    stealth = Stealth()
    async with stealth.use_async(async_playwright()) as p:
        try:
            headless = config.get("browser", {}).get("headless", False)
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            for seed in seed_keywords:
                try:
                    logger.info(f"Extracting Facebook terms for seed: {seed}")
                    terms = await _extract_facebook_terms_with_page(page, seed)

                    for rank, term in enumerate(terms):
                        kw = Keyword(
                            term=term,
                            suggestion_rank=rank + 1,
                            related_terms=[seed],
                            source="facebook_search"
                        )
                        db.upsert_keyword(kw)
                        all_keywords.append(kw)

                    # Small delay between seeds to avoid rate limiting
                    await asyncio.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Facebook keyword discovery failed for '{seed}': {e}")

            await browser.close()
        except Exception as e:
            logger.error(f"Failed to launch browser for Facebook keyword discovery: {e}")

    return all_keywords

async def _extract_facebook_terms_with_page(page: Page, keyword: str) -> list[str]:
    """
    Search Facebook using an existing page and extract common terms from results.
    """
    terms: list[str] = []

    try:
        # Navigate to Facebook search
        search_url = f"https://www.facebook.com/search/top?q={keyword}"
        await page.goto(search_url, timeout=30000)
        await asyncio.sleep(5)

        # Extract text from search results
        extracted = await page.evaluate("""
            () => {
                const results = [];
                const elements = document.querySelectorAll('span[role="heading"], a[role="link"]');
                for (const el of elements) {
                    const text = el.innerText.trim();
                    if (text && text.length > 5 && text.length < 50) {
                        results.push(text);
                    }
                }
                return results;
            }
        """)

        # Filter and deduplicate
        seen = set()
        for t in extracted:
            t_clean = t.lower()
            if t_clean not in seen and len(t_clean) > 5:
                seen.add(t_clean)
                terms.append(t)

    except Exception as e:
        logger.debug(f"Facebook DOM extraction failed for '{keyword}': {e}")

    return terms[:10]
