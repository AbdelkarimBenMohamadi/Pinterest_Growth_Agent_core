import asyncio
import json
import logging
import re
import unicodedata
from pathlib import Path
from playwright.async_api import async_playwright, Page, Response
from playwright_stealth import Stealth
from src.models import Trend
from src.store.database import Database
from src.utils.config import get_browser_config

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "pinterest", "explore", "sign up", "log in", "save", "share",
    "more", "home", "about", "all pins", "boards", "messages",
    "create", "watch", "notifications", "following", "followers",
    "more ideas", "everyday ideas", "popular", "trending",
    "get started", "welcome to", "discover", "find ideas",
    "skip to content", "search", "filter", "sort", "results",
    "all", "photos", "videos", "people", "boards", "pins",
}


def _is_valid_trend(text: str) -> bool:
    text = text.strip()
    if not text or len(text) < 3 or len(text) > 60:
        return False
    lower = text.lower()
    if lower in STOP_WORDS:
        return False
    if any(sw in lower for sw in ["skip", "sign up", "log in", "pinterest", "everyday"]):
        return False
    has_latin = bool(re.search(r"[a-zA-Z]", text))
    has_arabic = bool(re.search(r"[\u0600-\u06FF]", text))
    if has_arabic and not has_latin:
        return False
    if has_arabic:
        return False
    try:
        ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
        if ratio < 0.5:
            return False
    except Exception:
        pass
    return True


async def fetch_trends(categories: list[str], db: Database, config: dict, page: Page | None = None) -> list[Trend]:
    all_trends: list[Trend] = []
    scraper_mode = config.get("scraper", {}).get("mode", "safe").lower().strip()
    browser_mode = get_browser_config(config)["mode"]

    if page is not None and browser_mode == "gui" and scraper_mode == "fast":
        logger.warning("Ignoring scraper.mode=fast in GUI shared-page mode; using safe sequential trend scraping")
        scraper_mode = "safe"

    if scraper_mode != "fast":
        return await _fetch_trends_safe(categories, db, config, page=page)

    async def _process_category(category: str) -> list[Trend]:
        """Process a single category — runs in parallel with others."""
        try:
            trends = await _extract_trends_from_page(category, config)
            return _store_category_trends(category, trends, db)
        except Exception as e:
            logger.warning(f"Failed to fetch trends for '{category}': {e}")
            return []

    # Run all categories in parallel
    results = await asyncio.gather(
        *[_process_category(cat) for cat in categories],
        return_exceptions=True
    )

    for result in results:
        if isinstance(result, list):
            all_trends.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f"Parallel trend fetch failed: {result}")

    return all_trends


async def _fetch_trends_safe(categories: list[str], db: Database, config: dict, page: Page | None = None) -> list[Trend]:
    """Process trend categories sequentially in one browser window/context."""
    logger.info("Trend scraper running in safe sequential mode")
    all_trends: list[Trend] = []

    if page is not None:
        logger.info("Trend scraper reusing shared Pinterest browser page")
        for category in categories:
            try:
                trends = await _extract_trends_with_page(page, category)
                stored = _store_category_trends(category, trends, db)
                all_trends.extend(stored)
                logger.info(f"Found {len(stored)} valid trends for '{category}'")
                await asyncio.sleep(config.get("scraper", {}).get("safe_delay_seconds", 2))
            except Exception as e:
                logger.warning(f"Failed to fetch trends for '{category}': {e}")
        return all_trends

    stealth = Stealth()

    async with stealth.use_async(async_playwright()) as p:
        browser = None
        context = None
        try:
            browser_cfg = get_browser_config(config)
            browser = await p.chromium.launch(
                headless=browser_cfg["headless"],
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )

            session_file = Path(browser_cfg["session_file"])
            storage = str(session_file) if session_file.exists() else None
            context = await browser.new_context(
                storage_state=storage,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = await context.new_page()

            for category in categories:
                try:
                    trends = await _extract_trends_with_page(page, category)
                    stored = _store_category_trends(category, trends, db)
                    all_trends.extend(stored)
                    logger.info(f"Found {len(stored)} valid trends for '{category}'")
                    await asyncio.sleep(config.get("scraper", {}).get("safe_delay_seconds", 2))
                except Exception as e:
                    logger.warning(f"Failed to fetch trends for '{category}': {e}")

        except Exception as e:
            logger.warning(f"Playwright safe trend scraping failed: {e}")
        finally:
            try:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except Exception:
                pass

    return all_trends


async def _extract_trends_from_page(category: str, config: dict) -> list[dict]:
    """Extract trend suggestions from Pinterest using an isolated browser."""
    stealth = Stealth()

    async with stealth.use_async(async_playwright()) as p:
        browser = None
        context = None
        try:
            browser_cfg = get_browser_config(config)
            browser = await p.chromium.launch(
                headless=browser_cfg["headless"],
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )

            session_file = Path(browser_cfg["session_file"])
            storage = str(session_file) if session_file.exists() else None
            context = await browser.new_context(
                storage_state=storage,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = await context.new_page()
            return await _extract_trends_with_page(page, category)
        except Exception as e:
            logger.warning(f"Playwright trends extraction failed for '{category}': {e}")
            return []
        finally:
            try:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except Exception:
                pass


async def _extract_trends_with_page(page: Page, category: str) -> list[dict]:
    """Extract trend suggestions on an existing Pinterest page."""
    trends: list[dict] = []

    async def _on_response(response: Response) -> None:
        url = response.url
        if "AdvancedTypeahead" in url and response.request.method == "GET":
            try:
                data = await response.json()
                items = data.get("resource_response", {}).get("data", {}).get("items", [])
                for item in items:
                    if isinstance(item, dict) and "query" in item:
                        query = item["query"].strip()
                        if _is_valid_trend(query):
                            trends.append({"name": query, "velocity": 2.0})
            except Exception as e:
                logger.debug(f"Failed to parse AdvancedTypeahead response: {e}")

    page.on("response", _on_response)
    try:
        await page.goto(f"https://www.pinterest.com/search/pins/?q={category}", timeout=30000)
        await asyncio.sleep(4)

        partial = category.split()[0] if category else ""
        if partial:
            search_box = page.locator('input[data-test-id="search-box-input"]').first
            if await search_box.count() > 0:
                await search_box.click()
                await asyncio.sleep(0.5)
                await search_box.fill("")
                for char in partial:
                    await page.keyboard.press(char)
                    await asyncio.sleep(0.08)
                await asyncio.sleep(2)

        if len(trends) < 3:
            dom_trends = await _scrape_trends_from_dom(page, category)
            for t in dom_trends:
                if not any(existing["name"].lower() == t["name"].lower() for existing in trends):
                    trends.append(t)
    finally:
        try:
            page.remove_listener("response", _on_response)
        except Exception:
            pass

    return trends[:10]


def _store_category_trends(category: str, trends: list[dict], db: Database) -> list[Trend]:
    category_trends: list[Trend] = []
    for item in trends:
        name = ""
        velocity = 1.3
        keywords: list[str] = []

        if isinstance(item, str):
            if _is_valid_trend(item):
                name = item.strip()
            else:
                continue
        elif isinstance(item, dict):
            name = item.get("name", "")
            if not _is_valid_trend(name):
                continue
            velocity = item.get("velocity", 1.3)
            keywords = item.get("keywords", [])

        if name:
            trend = Trend(
                name=name,
                velocity=velocity,
                region="global",
                category=category,
                keywords=keywords,
            )
            db.insert_trend(trend)
            category_trends.append(trend)

    return category_trends


async def _scrape_trends_from_dom(page: Page, category: str) -> list[dict]:
    """Extract trend names from search results page DOM (page already navigated)."""
    trends: list[dict] = []

    try:

        for scroll in range(3):
            await page.evaluate(f"window.scrollTo(0, {(scroll + 1) * 600})")
            await asyncio.sleep(1.5)

        pin_texts = await page.evaluate("""
            () => {
                const items = [];
                const seen = new Set();
                const arabicRe = /[\\u0600-\\u06FF]/;

                const pinLinks = document.querySelectorAll('a[href*="/pin/"]');
                for (const link of pinLinks) {
                    const text = (link.textContent || '').trim();
                    if (text && text.length > 5 && text.length < 100 && !arabicRe.test(text)) {
                        const lines = text.split(/[\\n|]/).map(l => l.trim()).filter(l => l.length > 3 && l.length < 60 && !arabicRe.test(l));
                        for (const line of lines) {
                            if (!seen.has(line.toLowerCase())) {
                                seen.add(line.toLowerCase());
                                items.push(line);
                            }
                        }
                    }
                }

                const headings = document.querySelectorAll('h2, h3');
                for (const h of headings) {
                    const text = (h.textContent || '').trim();
                    if (text && text.length > 3 && text.length < 60 && !seen.has(text.toLowerCase())) {
                        seen.add(text.toLowerCase());
                        items.push(text);
                    }
                }

                return items;
            }
        """)

        for text in pin_texts:
            text = text.strip()
            if _is_valid_trend(text):
                trends.append({"name": text, "velocity": 1.0})

    except Exception as e:
        logger.debug(f"Search page scraping failed for '{category}': {e}")

    return trends
