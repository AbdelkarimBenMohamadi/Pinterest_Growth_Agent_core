import asyncio
import json
import random
import logging
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page, Response
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

# Use a separate session file for Twitter
TWITTER_SESSION_FILE = Path("data/twitter_session.json")

class TwitterClient:
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
            storage = str(TWITTER_SESSION_FILE) if TWITTER_SESSION_FILE.exists() else None

            self._context = await self._browser.new_context(
                storage_state=storage,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )

            self._page = await self._context.new_page()
        except Exception:
            logger.error("Failed to create Twitter browser context — cleaning up")
            await self.close()
            raise

        return self._page

    async def _save_session(self) -> None:
        if self._context:
            TWITTER_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(TWITTER_SESSION_FILE))
            logger.info("Twitter session saved to %s", TWITTER_SESSION_FILE)

    async def _random_delay(self, min_s: float = 2.0, max_s: float = 5.0) -> None:
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def login(self) -> bool:
        page = await self._launch()

        try:
            await page.goto("https://twitter.com/home", timeout=30000)
            await self._random_delay(3, 6)

            # Check if already logged in (look for tweet box or profile)
            if await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count() > 0:
                logger.info("Already logged in to Twitter (session restored)")
                return True

            logger.info("Twitter session not valid. Performing fresh login...")

            # Note: We need a get_twitter_credentials helper later
            import os
            username = os.getenv("TWITTER_USERNAME")
            password = os.getenv("TWITTER_PASSWORD")

            if not username or not password:
                logger.error("TWITTER_USERNAME and TWITTER_PASSWORD must be set in .env")
                return False

            await page.goto("https://twitter.com/i/flow/login", timeout=30000)
            await self._random_delay(3, 5)

            # Username
            user_input = page.locator('input[autocomplete="username"]')
            await user_input.fill(username)
            await page.keyboard.press("Enter")
            await self._random_delay(2, 3)

            # Password
            pass_input = page.locator('input[name="password"]')
            await pass_input.fill(password)
            await page.keyboard.press("Enter")
            await self._random_delay(6, 10)

            if await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count() > 0:
                await self._save_session()
                logger.info("Twitter login successful. Session saved.")
                return True
            else:
                logger.error("Twitter login failed")
                return False

        except Exception as e:
            logger.error(f"Twitter login error: {e}")
            return False

    async def post_tweet(self, text: str, image_path: str = None) -> bool:
        page = await self._launch()

        try:
            await page.goto("https://twitter.com/home", timeout=30000)
            await self._random_delay(3, 5)

            # Click tweet box
            tweet_box = page.locator('[data-testid="tweetTextarea_0"]').first
            await tweet_box.click()
            await tweet_box.fill(text)
            await self._random_delay(1, 2)

            if image_path:
                # Add image
                file_input = page.locator('input[data-testid="fileInput"]').first
                await file_input.set_input_files(image_path)
                await self._random_delay(3, 5)

            # Click Post button
            post_btn = page.locator('[data-testid="tweetButtonInline"]').first
            await post_btn.click()
            await self._random_delay(5, 8)

            logger.info("Tweet successful")
            return True

        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
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
