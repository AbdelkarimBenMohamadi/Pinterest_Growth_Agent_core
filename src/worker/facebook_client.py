import asyncio
import random
import logging
from playwright.async_api import async_playwright, BrowserContext, Page
from playwright_stealth import stealth

logger = logging.getLogger(__name__)

class FacebookClient:
    def __init__(self, config: dict):
        self.config = config
        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def _launch(self) -> Page:
        if self._page is not None:
            return self._page

        self._playwright = await async_playwright().start()

        headless = self.config.get("browser", {}).get("headless", False)

        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )

        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self._page = await self._context.new_page()
        await stealth(self._page)
        return self._page

    async def login(self, email, password) -> bool:
        page = await self._launch()
        try:
            await page.goto("https://www.facebook.com/", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # Handle cookie consent if it appears
            try:
                consent_btn = page.locator('button[data-testid="cookie-policy-manage-dialog-accept-button"]').first
                if await consent_btn.is_visible():
                    await consent_btn.click()
            except:
                pass

            await page.fill('input[id="email"]', email)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.fill('input[id="pass"]', password)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.click('button[name="login"]')

            await asyncio.sleep(random.uniform(5, 8))

            if "checkpoint" in page.url:
                logger.warning("Facebook login checkpoint detected (2FA/Security). Manual intervention required.")
                return False

            return True
        except Exception as e:
            logger.error(f"Facebook login failed: {e}")
            return False

    async def post_to_page(self, page_url: str, text: str, image_path: str = None):
        """Prototype for posting to a Facebook Page."""
        page = await self._launch()
        try:
            await page.goto(page_url)
            await asyncio.sleep(random.uniform(3, 5))

            # This is a very simplified prototype as FB selectors change frequently
            # and differ between desktop/mobile/business suite views.
            logger.info(f"Drafting post on {page_url}...")
            # Logic for finding 'Create post' button and filling it would go here

        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
