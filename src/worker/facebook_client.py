import asyncio
import json
import random
import logging
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page, Response
from playwright_stealth import Stealth
from src.models import FacebookMetadata

logger = logging.getLogger(__name__)

# Use a separate session file for Facebook to avoid conflicts
FB_SESSION_FILE = Path("data/facebook_session.json")

class FacebookClient:
    def __init__(self, config: dict, db=None):
        self.config = config
        self.db = db
        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._stealth = Stealth()

    async def _launch(self) -> Page:
        if self._page is not None:
            return self._page

        pw_ctx = self._stealth.use_async(async_playwright())
        self._playwright = await pw_ctx.start()

        headless = self.config.get("browser", {}).get("headless", False)

        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )

        try:
            storage = str(FB_SESSION_FILE) if FB_SESSION_FILE.exists() else None

            self._context = await self._browser.new_context(
                storage_state=storage,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )

            self._page = await self._context.new_page()
        except Exception:
            logger.error("Failed to create browser context or page — cleaning up")
            await self.close()
            raise

        return self._page

    async def _save_session(self) -> None:
        if self._context:
            FB_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(FB_SESSION_FILE))
            logger.info("Facebook session saved to %s", FB_SESSION_FILE)

    async def _random_delay(self, min_s: float = 2.0, max_s: float = 5.0) -> None:
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def login(self) -> bool:
        page = await self._launch()

        try:
            await page.goto("https://www.facebook.com/", timeout=30000)
            await self._random_delay(3, 6)

            # Check if already logged in (look for search input or profile icon)
            if await page.locator('div[role="search"]').count() > 0 or await page.locator('div[aria-label*="Your profile" i]').count() > 0:
                logger.info("Already logged in to Facebook (session restored)")
                return True

            logger.info("Facebook session not valid. Performing fresh login...")

            from src.utils.config import get_facebook_credentials
            email, password = get_facebook_credentials()

            email_input = page.locator('input[id="email"]')
            await email_input.fill(email)
            await self._random_delay(0.5, 1.0)

            password_input = page.locator('input[id="pass"]')
            await password_input.fill(password)
            await self._random_delay(0.5, 1.0)

            login_button = page.locator('button[name="login"]')
            await login_button.click()

            await self._random_delay(6, 10)

            if await page.locator('div[role="search"]').count() > 0:
                await self._save_session()
                logger.info("Facebook login successful. Session saved.")
                return True
            else:
                logger.error("Facebook login failed")
                return False

        except Exception as e:
            logger.error(f"Facebook login error: {e}")
            return False

    async def post_content(self, text: str, image_path: str = None) -> bool:
        page = await self._launch()

        try:
            # Check if we should post to a specific page
            page_id = self.config.get("account", {}).get("facebook_page_id")
            if page_id:
                logger.info(f"Navigating to Facebook Page: {page_id}")
                await page.goto(f"https://www.facebook.com/{page_id}", timeout=30000)
            else:
                await page.goto("https://www.facebook.com/", timeout=30000)

            await self._random_delay(3, 5)

            # Click "What's on your mind?"
            post_trigger = page.locator('div[role="button"]:has-text("What\'s on your mind?"), div[role="button"]:has-text("بم تفكر؟"), div[role="button"]:has-text("Create post")').first
            await post_trigger.click()
            await self._random_delay(2, 3)

            # Fill text
            text_area = page.locator('div[role="textbox"][aria-label*="What\'s on your mind?" i], div[role="textbox"][aria-label*="بم تفكر؟" i], div[role="textbox"][aria-label*="Create a post" i]').first
            await text_area.fill(text)
            await self._random_delay(1, 2)

            if image_path:
                # Add photo/video
                photo_button = page.locator('div[aria-label*="Photo/video" i], div[aria-label*="صور/فيديو" i]').first
                await photo_button.click()
                await self._random_delay(1, 2)

                file_input = page.locator('input[type="file"][accept*="image" i]').first
                await file_input.set_input_files(image_path)
                await self._random_delay(3, 5)

            # Click Post
            post_button = page.locator('div[role="button"][aria-label*="Post" i], div[role="button"][aria-label*="نشر" i]').first
            await post_button.click()
            await self._random_delay(5, 8)

            logger.info("Facebook post successful")
            return True

        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            return False

    async def close(self) -> None:
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
