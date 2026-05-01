import asyncio
import json
import logging
import random
import re
from pathlib import Path
from playwright.async_api import async_playwright, Page, Response
from playwright_stealth import Stealth
from src.models import Keyword
from src.store.database import Database
from src.utils.constants import SESSION_FILE

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "skip to content", "pinterest", "home", "search", "explore", "about",
    "blog", "terms", "privacy", "help", "copyright", "cookies",
    "close", "open", "menu", "back", "next", "continue", "sign up",
    "log in", "login", "register", "notifications", "profile",
    "following", "followers", "boards", "pins", "messages",
    "find ideas for", "join pinterest", "i already have an account",
    "bring your", "with pinterest", "search by skin tone",
    " تصفح", "حساب", "تسجيل", "دخول", "المحتوى", "تتخط", "إلى",
    "كل المنشورات", "all pins", "all boards", "more ideas",
    "everyday ideas", "popular", "trending", "get started",
    "welcome to", "discover", "create", "watch",
}

BAD_PREFIXES = {
    "already", "continue", "skip", "sign", "log", "about",
    "discover", "find", "join", "welcome", "get",
}

BAD_PATTERNS = {
    r"^\W+$",           # only non-word chars
    r"^\d+$",            # only digits
    r"^[\u0600-\u06FF]",  # Arabic text
}


def _is_valid_keyword(term: str) -> bool:
    term_lower = term.lower().strip()
    if not term_lower or len(term_lower) <= 3 or len(term_lower) > 50:
        return False
    if term_lower in STOP_WORDS:
        return False
    if any(term_lower.startswith(bp) for bp in BAD_PREFIXES):
        return False
    for pattern in BAD_PATTERNS:
        if re.match(pattern, term_lower):
            return False
    # Must contain at least one letter
    if not re.search(r"[a-zA-Z]", term_lower):
        return False
    return True


async def scrape_keywords(seed_keywords: list[str], db: Database, config: dict) -> list[Keyword]:
    all_keywords: list[Keyword] = []

    async def _process_seed(seed: str) -> list[Keyword]:
        """Process a single seed keyword — runs in parallel with others."""
        seed_keywords_result: list[Keyword] = []
        try:
            keywords = await _extract_keywords_from_page(seed, config)

            seen = set()
            for rank, term in enumerate(keywords):
                if not _is_valid_keyword(term):
                    continue
                term_lower = term.lower().strip()
                if term_lower in seen:
                    continue
                seen.add(term_lower)

                kw = Keyword(
                    term=term.strip(),
                    suggestion_rank=rank + 1,
                    related_terms=[seed],
                    source="autosuggest"
                )
                db.upsert_keyword(kw)
                seed_keywords_result.append(kw)

            logger.info(f"Found {len(seed_keywords_result)} valid keywords for '{seed}'")

        except Exception as e:
            logger.warning(f"Failed to scrape '{seed}': {e}")

        return seed_keywords_result

    # Run all seed keywords in parallel
    results = await asyncio.gather(
        *[_process_seed(seed) for seed in seed_keywords],
        return_exceptions=True
    )

    for result in results:
        if isinstance(result, list):
            all_keywords.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f"Parallel seed scrape failed: {result}")

    return all_keywords


async def _extract_keywords_from_page(keyword: str, config: dict) -> list[str]:
    """Extract keyword suggestions from Pinterest using API interception + DOM scraping."""
    suggestions: list[str] = []
    stealth = Stealth()
    api_suggestions: list[str] = []

    async def _on_response(response: Response) -> None:
        url = response.url
        if "AdvancedTypeahead" in url and response.request.method == "GET":
            try:
                data = await response.json()
                extracted = _parse_suggestion_api(data)
                api_suggestions.extend(extracted)
            except Exception as e:
                logger.debug(f"Failed to parse AdvancedTypeahead response: {e}")

    async with stealth.use_async(async_playwright()) as p:
        try:
            headless = config.get("browser", {}).get("headless", False)
            browser = await p.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )

            storage = str(SESSION_FILE) if SESSION_FILE.exists() else None
            context = await browser.new_context(
                storage_state=storage,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = await context.new_page()
            page.on("response", _on_response)

            # Navigate to Pinterest search
            await page.goto(f"https://www.pinterest.com/search/pins/?q={keyword}", timeout=30000)
            await asyncio.sleep(4)

            # Strategy 1: Type into search bar to trigger autocomplete
            autocomplete_kw = await _try_autocomplete(page, keyword)
            if autocomplete_kw:
                suggestions.extend(autocomplete_kw)

            # If API interception gave us suggestions, use those
            if api_suggestions:
                suggestions.extend(api_suggestions)

            # Strategy 2: DOM scraping of search results (broad selectors)
            if len(suggestions) < 5:
                dom_suggestions = await _scrape_dom_suggestions(page)
                suggestions.extend(dom_suggestions)

            # Strategy 3: Scrape "Related searches" section
            if len(suggestions) < 5:
                related = await _scrape_related_searches(page)
                suggestions.extend(related)

            await context.close()
            await browser.close()

        except Exception as e:
            logger.warning(f"Playwright extraction failed for '{keyword}': {e}")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in suggestions:
        s_lower = s.lower().strip()
        if s_lower not in seen:
            seen.add(s_lower)
            unique.append(s.strip())

    return unique[:15]


async def _try_autocomplete(page: Page, keyword: str) -> list[str]:
    """Type into search bar and capture autocomplete suggestions."""
    suggestions: list[str] = []

    try:
        # Click the search bar
        search_bar = page.locator(
            'input[aria-label*="search" i], input[aria-label*="Search" i], '
            'input[name="searchBox"], input[data-test-id="search-input"], '
            'input[placeholder*="search" i]'
        ).first

        if await search_bar.count() > 0:
            await search_bar.click()
            await asyncio.sleep(0.5)

            # Clear any existing text
            await search_bar.fill("")
            await asyncio.sleep(0.3)

            # Type the seed keyword character by character to trigger autocomplete
            for char in keyword[:20]:
                await page.keyboard.press(char)
                await asyncio.sleep(random.uniform(0.05, 0.1))

            await asyncio.sleep(2)  # Wait for autocomplete to load

            # Extract suggestions from the autocomplete dropdown
            suggestion_texts = await page.evaluate("""
                () => {
                    const items = [];

                    // Look for autocomplete/typeahead dropdown items
                    const selectors = [
                        '[data-test-id="typeahead-item"]',
                        '[role="listbox"] [role="option"]',
                        '[role="listbox"] li',
                        '.typeahead-item',
                        '[class*="suggestion"]',
                        '[class*="autocomplete"] li',
                        '[class*="search-suggestion"]',
                        'ul[class*="dropdown"] li',
                        'div[class*="suggestions"] span',
                        'div[class*="Suggestion"] span',
                    ];

                    for (const sel of selectors) {
                        const els = document.querySelectorAll(sel);
                        for (const el of els) {
                            const text = (el.textContent || '').trim();
                            if (text && text.length > 3 && text.length < 60) {
                                items.push(text);
                            }
                        }
                    }

                    return items;
                }
            """)

            for text in suggestion_texts:
                if _is_valid_keyword(text):
                    suggestions.append(text.strip())

    except Exception as e:
        logger.debug(f"Autocomplete extraction failed for '{keyword}': {e}")

    return suggestions


async def _scrape_dom_suggestions(page: Page) -> list[str]:
    """Extract pin titles from the search results page using broad DOM selectors."""
    suggestions: list[str] = []

    # Scroll to load more pins
    for i in range(3):
        await page.evaluate(f"window.scrollTo(0, {(i + 1) * 600})")
        await asyncio.sleep(1.5)

    pin_texts = await page.evaluate("""
        () => {
            const items = [];
            const seen = new Set();

            // Strategy 1: Get text from pin links
            const pinLinks = document.querySelectorAll('a[href*="/pin/"]');
            for (const link of pinLinks) {
                const text = (link.textContent || '').trim();
                if (text && text.length > 3) {
                    // Pin card text may contain multiple lines - take the most relevant short ones
                    const lines = text.split(/[\\n|]/).map(l => l.trim()).filter(l => l.length > 3 && l.length < 60);
                    for (const line of lines) {
                        if (!seen.has(line.toLowerCase())) {
                            seen.add(line.toLowerCase());
                            items.push(line);
                        }
                    }
                }
            }

            // Strategy 2: Get text from heading-like elements within pin cards
            const headings = document.querySelectorAll('h2, h3, h4');
            for (const h of headings) {
                const text = (h.textContent || '').trim();
                if (text && text.length > 3 && text.length < 60 && !seen.has(text.toLowerCase())) {
                    seen.add(text.toLowerCase());
                    items.push(text);
                }
            }

            // Strategy 3: Find elements that contain typical pin title text lengths
            const spans = document.querySelectorAll('span, p, div[role="heading"]');
            for (const el of spans) {
                // Only get direct text (not nested)
                const text = (el.childNodes.length <= 2 ? el.textContent : '').trim();
                if (text && text.length > 5 && text.length < 50 && !seen.has(text.toLowerCase())) {
                    seen.add(text.toLowerCase());
                    items.push(text);
                }
            }

            return items.slice(0, 20);
        }
    """)

    for text in pin_texts:
        if _is_valid_keyword(text):
            suggestions.append(text.strip())

    return suggestions


async def _scrape_related_searches(page: Page) -> list[str]:
    """Look for a 'Related searches' or similar section on the search results page."""
    suggestions: list[str] = []

    try:
        related = await page.evaluate("""
            () => {
                const items = [];

                // Pinterest often shows related search chips/pills at the top or bottom of results
                const chips = document.querySelectorAll(
                    'a[href*="q="], [role="button"][href*="search"], '
                    + 'div[class*="related"] a, div[class*="Related"] a, '
                    + 'span[class*="chip"], div[class*="chip"] span'
                );

                for (const chip of chips) {
                    const text = (chip.textContent || '').trim();
                    if (text && text.length > 2 && text.length < 40) {
                        items.push(text);
                    }
                }

                // Also check for Guided Search / filter sections
                const filters = document.querySelectorAll(
                    'div[data-test-id="filter-item"], '
                    + 'a[data-test-id="search-suggestion"]'
                );
                for (const f of filters) {
                    const text = (f.textContent || '').trim();
                    if (text && text.length > 2 && text.length < 40) {
                        items.push(text);
                    }
                }

                return items;
            }
        """)

        for text in related:
            if _is_valid_keyword(text):
                suggestions.append(text.strip())

    except Exception as e:
        logger.debug(f"Related search scraping failed: {e}")

    return suggestions


def _parse_suggestion_api(data: dict) -> list[str]:
    """Parse Pinterest AdvancedTypeaheadResource API response for suggestion terms."""
    suggestions: list[str] = []

    try:
        items = data.get("resource_response", {}).get("data", {}).get("items", [])
        for item in items:
            if isinstance(item, dict) and "query" in item:
                query = item["query"].strip()
                if len(query) > 2:
                    suggestions.append(query)
            elif isinstance(item, str):
                s = item.strip()
                if len(s) > 2:
                    suggestions.append(s)

    except Exception as e:
        logger.debug(f"Suggestion API parsing failed: {e}")

    return suggestions


