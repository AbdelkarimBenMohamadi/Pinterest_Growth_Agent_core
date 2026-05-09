import asyncio
import json
import random
import logging
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page, Response
from playwright_stealth import Stealth
from src.models import InstagramMetadata

logger = logging.getLogger(__name__)

# Use a separate session file for Instagram
INSTA_SESSION_FILE = Path("data/instagram_session.json")

class InstagramClient:
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
            storage = str(INSTA_SESSION_FILE) if INSTA_SESSION_FILE.exists() else None

            # Instagram often works better with a mobile user agent for simple interactions
            self._context = await self._browser.new_context(
                storage_state=storage,
                viewport={"width": 375, "height": 812},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
                is_mobile=True,
                has_touch=True,
                locale="en-US",
            )

            self._page = await self._context.new_page()
        except Exception:
            logger.error("Failed to create Instagram browser context — cleaning up")
            await self.close()
            raise

        return self._page

    async def _save_session(self) -> None:
        if self._context:
            INSTA_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(INSTA_SESSION_FILE))
            logger.info("Instagram session saved to %s", INSTA_SESSION_FILE)

    async def _random_delay(self, min_s: float = 2.0, max_s: float = 5.0) -> None:
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def login(self) -> bool:
        page = await self._launch()

        try:
            await page.goto("https://www.instagram.com/", timeout=30000)
            await self._random_delay(3, 6)

            # Check if already logged in (look for new post button or profile)
            if await page.locator('svg[aria-label="New post"]').count() > 0 or await page.locator('svg[aria-label="Profile"]').count() > 0:
                logger.info("Already logged in to Instagram (session restored)")
                return True

            logger.info("Instagram session not valid. Performing fresh login...")

            from src.utils.config import get_instagram_credentials
            username, password = get_instagram_credentials()

            # Fill login form
            # On mobile, the fields might be different
            user_input = page.locator('input[name="username"]')
            await user_input.fill(username)
            await self._random_delay(0.5, 1.0)

            pass_input = page.locator('input[name="password"]')
            await pass_input.fill(password)
            await self._random_delay(0.5, 1.0)

            login_btn = page.locator('button[type="submit"]')
            await login_btn.click()

            await self._random_delay(6, 10)

            # Handle "Save Login Info?"
            try:
                save_info_btn = page.locator('button:has-text("Not Now"), button:has-text("ليس الآن")').first
                if await save_info_btn.is_visible(timeout=5000):
                    await save_info_btn.click()
            except Exception:
                pass

            if await page.locator('svg[aria-label="New post"]').count() > 0 or await page.locator('svg[aria-label="Home"]').count() > 0:
                await self._save_session()
                logger.info("Instagram login successful. Session saved.")
                return True
            else:
                logger.error("Instagram login failed")
                return False

        except Exception as e:
            logger.error(f"Instagram login error: {e}")
            return False

    async def post_content(self, image_path: str, caption: str) -> bool:
        """
        Post a photo to Instagram.
        Note: Automation of Instagram posting via browser can be tricky and subject to change.
        """
        page = await self._launch()

        try:
            await page.goto("https://www.instagram.com/", timeout=30000)
            await self._random_delay(3, 5)

            # Click "New Post"
            new_post_btn = page.locator('svg[aria-label="New post"], div[role="menuitem"]:has(svg[aria-label="New post"])').first
            await new_post_btn.click()
            await self._random_delay(2, 3)

            # Select from computer (file input)
            # Instagram often uses a hidden file input
            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files(image_path)
            await self._random_delay(3, 5)

            # Click "Next"
            next_btn = page.locator('button:has-text("Next"), button:has-text("التالي")').first
            await next_btn.click()
            await self._random_delay(2, 3)

            # Click "Next" again (filters page)
            await next_btn.click()
            await self._random_delay(2, 3)

            # Fill caption
            caption_area = page.locator('div[aria-label*="Write a caption" i], textarea[aria-label*="Write a caption" i]').first
            await caption_area.fill(caption)
            await self._random_delay(1, 2)

            # Click "Share"
            share_btn = page.locator('button:has-text("Share"), button:has-text("مشاركة")').first
            await share_btn.click()

            # Wait for upload to complete
            await asyncio.sleep(10)

            logger.info("Instagram post successful")
            return True

        except Exception as e:
            logger.error(f"Failed to post to Instagram: {e}")
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
