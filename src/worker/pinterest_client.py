import asyncio
import json
import random
import re
import logging
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page, Response
from playwright_stealth import Stealth
from src.models import PinMetadata, EngagementData
from src.utils.config import get_pinterest_credentials
from src.utils.constants import SESSION_FILE

logger = logging.getLogger(__name__)



class PinterestClient:
    def __init__(self, config: dict, db=None):
        self.config = config
        self.db = db
        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._stealth = Stealth()
        self._username: str = ""

    async def _launch(self) -> Page:
        if self._page is not None:
            return self._page

        pw_ctx = self._stealth.use_async(async_playwright())
        self._playwright = await pw_ctx.start()

        headless = self.config.get("browser", {}).get("headless", False)
        profile_path = self.config.get("browser", {}).get("chrome_profile_path")

        if profile_path:
            logger.info(f"Launching with persistent Chrome profile: {profile_path}")
            # Note: launch_persistent_context returns a BrowserContext directly
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=headless,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ]
            )
            # Use the first page or create a new one
            if self._context.pages:
                self._page = self._context.pages[0]
            else:
                self._page = await self._context.new_page()
        else:
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ]
            )

            try:
                storage = str(SESSION_FILE) if SESSION_FILE.exists() else None

                self._context = await self._browser.new_context(
                    storage_state=storage,
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-US",
                )

                self._page = await self._context.new_page()
            except Exception:
                # If context or page creation fails, clean up the browser to prevent leaks
                logger.error("Failed to create browser context or page — cleaning up")
                await self.close()
                raise

        return self._page

    async def _save_session(self) -> None:
        if self._context:
            SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(SESSION_FILE))
            logger.info("Session saved to %s", SESSION_FILE)

    async def _random_delay(self, min_s: float = 2.0, max_s: float = 5.0) -> None:
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def _get_username(self, page: Page) -> str:
        if self._username:
            return self._username
        try:
            await page.goto("https://www.pinterest.com/me/", timeout=15000)
            await self._random_delay(2, 3)
            url = page.url
            match = re.search(r"pinterest\.com/([^/]+)", url)
            if match:
                self._username = match.group(1)
                logger.info(f"Detected username: {self._username}")
        except Exception as e:
            logger.warning(f"Could not detect username: {e}")
        return self._username

    # ── Login ──────────────────────────────────────────────

    async def login(self) -> bool:
        page = await self._launch()

        try:
            await page.goto("https://www.pinterest.com/", timeout=30000)
            await self._random_delay(3, 6)

            await page.goto("https://www.pinterest.com/me/", timeout=15000)
            await self._random_delay(2, 4)
            current_url = page.url

            if "/login" not in current_url:
                match = re.search(r"pinterest\.com/([^/]+)", current_url)
                if match and match.group(1) not in ("me", "login", "signup", ""):
                    self._username = match.group(1)
                logger.info(f"Already logged in (session restored) — profile: {current_url}")
                return True

            logger.info("Session not valid. Performing fresh login...")
            await page.goto("https://www.pinterest.com/login/", timeout=30000)
            await self._random_delay(2, 4)

            email_input = page.locator('input[id="email"]')
            try:
                await email_input.wait_for(state="visible", timeout=10000)
            except Exception:
                email_input = page.locator('input[name="id"], input[type="email"]').first
                await email_input.wait_for(state="visible", timeout=10000)

            email, password = get_pinterest_credentials()

            await email_input.click()
            await self._random_delay(0.5, 1.0)
            for char in email:
                await email_input.press(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            await self._random_delay(0.5, 1.5)

            password_input = page.locator('input[id="password"]')
            await password_input.click()
            await self._random_delay(0.5, 1.0)
            for char in password:
                await password_input.press(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            await self._random_delay(1.0, 2.0)

            login_button = page.locator('button[type="submit"]')
            await login_button.click()

            await self._random_delay(6, 10)

            current_url = page.url
            if "/login" in current_url:
                logger.error("Login failed — still on login page")
                return False

            await self._save_session()
            logger.info("Login successful. Session saved.")
            return True

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    # ── Pin Posting ────────────────────────────────────────

    async def post_pin(self, image_path: str, metadata: PinMetadata, board: str, destination_link: str = "") -> str:
        page = await self._launch()

        pin_create_data: dict = {"pin_id": None, "pin_url": None}
        pin_create_event = asyncio.Event()

        async def _on_response(response: Response) -> None:
            url = response.url
            method = response.request.method
            if method != "POST":
                return
            if not any(p in url.lower() for p in ["/v3/pins", "pinresource/create", "pin-builder", "/resource/pin"]):
                return
            try:
                data = await response.json()
                pin_data = data
                if isinstance(data, dict):
                    if "resource_response" in data:
                        pin_data = data["resource_response"]
                    if isinstance(pin_data, dict) and "data" in pin_data:
                        pin_data = pin_data["data"]
                pin_id = None
                if isinstance(pin_data, dict):
                    pin_id = pin_data.get("id")
                if pin_id:
                    pin_create_data["pin_id"] = str(pin_id)
                    pin_create_data["pin_url"] = f"https://www.pinterest.com/pin/{pin_id}/"
                    pin_create_event.set()
                    logger.info(f"Intercepted pin creation response: pin_id={pin_id}")
            except Exception:
                pass

        try:
            page.on("response", _on_response)

            await page.goto("https://www.pinterest.com/pin-creation-tool/", timeout=60000)
            await self._random_delay(3, 5)
            logger.info(f"Pin builder loaded: {page.url}")

            # Upload image
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(image_path, timeout=30000)
            await self._random_delay(4, 7)

            # Wait for form to appear after upload
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await self._random_delay(1, 2)

            # Scroll down so form fields are visible
            await page.evaluate("window.scrollTo(0, 300)")
            await self._random_delay(1, 2)

            # Fill title — try multiple selector strategies
            title_filled = await self._fill_title(page, metadata.title[:100])
            if not title_filled:
                logger.warning("Could not fill title field — pin will be posted without a title")
            await self._random_delay(1, 2)

            # Fill description
            await self._fill_description(page, metadata.description)
            await self._random_delay(1, 2)

            # Fill alt text
            await self._fill_alt_text(page, metadata.alt_text)
            await self._random_delay(0.5, 1)

            # Select board
            if board:
                await self._select_board(page, board)
                await self._random_delay(1, 2)

            # Fill destination link (clickable URL on the pin)
            if destination_link:
                await self._fill_destination_link(page, destination_link)
                await self._random_delay(1, 2)

            # Scroll to publish button
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self._random_delay(1, 2)

            # Click publish
            publish_btn = page.locator(
                'button:has-text("Publish"), button:has-text("Save"), button:has-text("نشر")'
            ).first
            try:
                await publish_btn.wait_for(state="visible", timeout=10000)
                await publish_btn.click(force=True)
                logger.info("Clicked publish button")
            except Exception as e:
                logger.warning(f"Publish button click failed: {e}. Trying Ctrl+Enter...")
                await page.keyboard.press("Control+Enter")

            # Wait for pin creation response from API using event (no polling race)
            try:
                await asyncio.wait_for(pin_create_event.wait(), timeout=20)
            except asyncio.TimeoutError:
                pass

            if pin_create_data["pin_id"]:
                pin_url = pin_create_data["pin_url"]
                logger.info(f"Pin posted successfully (API interception): {pin_url}")
                await self._save_session()
                return pin_url

            # Fallback 1: Try to extract pin URL from page JS state
            pin_url = await self._extract_pin_from_page_state(page)
            if pin_url:
                logger.info(f"Pin URL found from page state: {pin_url}")
                await self._save_session()
                return pin_url

            # Fallback 2: Navigate to user's profile pins page and find the newest pin
            logger.info("API interception failed. Trying profile pins page fallback...")
            pin_url = await self._find_newest_pin_on_profile(page)
            if pin_url:
                logger.info(f"Pin URL found from profile: {pin_url}")
                await self._save_session()
                return pin_url

            # Pin may have succeeded but we couldn't detect the URL
            logger.warning("Pin posted but URL could not be determined. Marking as 'posted_unknown'.")
            await self._save_session()
            return "posted_unknown"

        except Exception as e:
            logger.error(f"Failed to post pin: {e}")
            return ""

    async def _fill_title(self, page: Page, title: str) -> bool:
        if not title:
            return False

        strategies = [
            ("contenteditable-title", lambda: page.locator('div[contenteditable="true"][role="textbox"]').first),
            ("input-title", lambda: page.locator('input[id="pin-draft-title"]').first),
            ("input-name-title", lambda: page.locator('input[name="title"]').first),
            ("input-placeholder-title", lambda: page.locator('input[placeholder*="title" i]').first),
            ("input-placeholder-add-title", lambda: page.locator('input[placeholder*="Add a title" i]').first),
            ("h1-contenteditable", lambda: page.locator('h1[contenteditable="true"]').first),
        ]

        for name, locator_fn in strategies:
            try:
                loc = locator_fn()
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.scroll_into_view_if_needed()
                    await self._random_delay(0.3, 0.6)
                    await loc.click(force=True)
                    await self._random_delay(0.3, 0.5)
                    await loc.press_sequentially(title, delay=random.uniform(30, 70))
                    logger.info(f"Title filled via {name}")
                    return True
            except Exception:
                continue

        # JS fallback: find any visible contenteditable or input that looks like a title field
        try:
            filled = await page.evaluate(f"""
                () => {{
                    const editors = document.querySelectorAll('div[contenteditable="true"][role="textbox"]');
                    for (const el of editors) {{
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && rect.top < 600) {{
                            el.focus();
                            document.execCommand('selectAll', false, null);
                            document.execCommand('insertText', false, {json.dumps(title)});
                            el.dispatchEvent(new Event('input', {{bubbles: true}}));
                            el.dispatchEvent(new Event('change', {{bubbles: true}}));
                            return true;
                        }}
                    }}

                    const inputs = document.querySelectorAll('input[type="text"]');
                    for (const inp of inputs) {{
                        const ph = (inp.placeholder || '').toLowerCase();
                        if (ph.includes('title') || ph.includes('add a title') || inp.id.includes('title')) {{
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value'
                            ).set;
                            nativeInputValueSetter.call(inp, {json.dumps(title)});
                            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                            inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)
            if filled:
                logger.info("Title filled via JS fallback")
                return True
        except Exception as e:
            logger.debug(f"JS title fallback failed: {e}")

        logger.warning("Standard locators failed. Invoking Self-Healing Module for title...")
        from src.worker.self_healing import heal_locator
        healed_selector = await heal_locator(page, "the pin title input field", self.config, db=self.db)
        if healed_selector:
            try:
                loc = page.locator(healed_selector).first
                if await loc.is_visible():
                    await loc.scroll_into_view_if_needed()
                    await self._random_delay(0.3, 0.6)
                    await loc.click(force=True)
                    await self._random_delay(0.3, 0.5)
                    await loc.press_sequentially(title, delay=random.uniform(30, 70))
                    logger.info(f"Title filled via healed selector: {healed_selector}")
                    return True
            except Exception as e:
                logger.error(f"Healed title locator failed: {e}")

        return False

    async def _fill_description(self, page: Page, description: str) -> bool:
        if not description:
            return False

        # First, try the most specific locator for Pinterest's current description box
        try:
            desc_locator = page.locator('.public-DraftEditor-content, div[aria-label*="وصف" i], div[aria-label*="description" i]').first
            if await desc_locator.is_visible():
                await desc_locator.scroll_into_view_if_needed()
                await self._random_delay(0.3, 0.5)
                await desc_locator.click(force=True)
                await self._random_delay(0.3, 0.5)
                await page.keyboard.type(description, delay=random.uniform(20, 50))
                logger.info("Description filled via DraftEditor locator")
                return True
        except Exception:
            pass

        # Try fallback locators if the above fails
        try:
            all_textboxes = page.locator('div[role="textbox"], div[role="combobox"]')
            count = await all_textboxes.count()
            for i in range(count):
                try:
                    loc = all_textboxes.nth(i)
                    if await loc.is_visible():
                        box = await loc.bounding_box()
                        # Ignore the tiny empty text layer warning div
                        if box and box["height"] > 30 and box["width"] > 100:
                            await loc.scroll_into_view_if_needed()
                            await loc.click(force=True)
                            await self._random_delay(0.3, 0.5)
                            await page.keyboard.type(description, delay=random.uniform(20, 50))
                            logger.info(f"Description filled (fallback textbox index {i})")
                            return True
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: textarea
        try:
            desc_input = page.locator('textarea[name="description"]')
            if await desc_input.is_visible():
                await desc_input.fill(description)
                logger.info("Description filled via textarea")
                return True
        except Exception:
            pass

        logger.warning("Standard locators failed. Invoking Self-Healing Module for description...")
        from src.worker.self_healing import heal_locator
        healed_selector = await heal_locator(page, "the pin description text box", self.config, db=self.db)
        if healed_selector:
            try:
                loc = page.locator(healed_selector).first
                if await loc.is_visible():
                    await loc.scroll_into_view_if_needed()
                    await loc.click(force=True)
                    await self._random_delay(0.3, 0.5)
                    await loc.press_sequentially(description, delay=random.uniform(20, 50))
                    logger.info(f"Description filled via healed selector: {healed_selector}")
                    return True
            except Exception as e:
                logger.error(f"Healed description locator failed: {e}")

        logger.warning("Could not fill description field")
        return False

    async def _fill_alt_text(self, page: Page, alt_text: str) -> bool:
        if not alt_text:
            return False

        # Try clicking "More options" or "المزيد من الخيارات" accordion if it exists to reveal alt text
        try:
            more_options = page.locator('div:has-text("More options"), div:has-text("المزيد من الخيارات"), button:has-text("More options")').last
            if await more_options.is_visible():
                await more_options.click()
                await self._random_delay(0.5, 1.0)
        except Exception:
            pass

        locators = [
            page.locator('textarea[id="pin-draft-alttext"]').first,
            page.locator('textarea[placeholder*="alt" i]').first,
            page.locator('textarea[aria-label*="alt" i]').first,
            page.locator('textarea[placeholder*="بديل" i]').first,
            page.locator('textarea[aria-label*="بديل" i]').first,
            page.locator('input[placeholder*="بديل" i]').first,
            page.locator('input[aria-label*="بديل" i]').first,
        ]

        for loc in locators:
            try:
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.fill(alt_text)
                    logger.info("Alt text filled")
                    return True
            except Exception:
                continue

        logger.warning("Standard locators failed. Invoking Self-Healing Module for alt text...")
        from src.worker.self_healing import heal_locator
        healed_selector = await heal_locator(page, "the alt-text input field", self.config, db=self.db)
        if healed_selector:
            try:
                loc = page.locator(healed_selector).first
                if await loc.is_visible():
                    await loc.fill(alt_text)
                    logger.info(f"Alt text filled via healed selector: {healed_selector}")
                    return True
            except Exception as e:
                logger.error(f"Healed alt text locator failed: {e}")

        return False

    async def _select_board(self, page: Page, board: str) -> bool:
        try:
            board_btn = page.locator(
                'button[data-test-id="board-dropdown-select-button"], '
                'div[data-test-id="board-selector"] button, '
                'button[aria-label*="board" i]'
            ).first
            if await board_btn.count() > 0 and await board_btn.is_visible():
                await board_btn.click()
                await self._random_delay(1, 2)

                # Wait for board dropdown to appear and find the matching board
                board_option = page.locator(
                    f'div[data-test-id="board-row"] >> text="{board}"'
                ).first
                try:
                    await board_option.wait_for(state="visible", timeout=3000)
                    await board_option.click()
                    await self._random_delay(1, 2)
                    logger.info(f"Board '{board}' selected")
                    return True
                except Exception:
                    # Try typing board name in search
                    board_search = page.locator('input[placeholder*="Search" i], input[aria-label*="Search" i]').first
                    if await board_search.count() > 0 and await board_search.is_visible():
                        await board_search.fill(board)
                        await self._random_delay(1, 2)
                        first_result = page.locator('div[data-test-id="board-row"], div[role="option"]').first
                        if await first_result.count() > 0 and await first_result.is_visible():
                            await first_result.click()
                            logger.info(f"Board '{board}' selected via search")
                            return True
        except Exception as e:
            logger.warning(f"Board selection failed: {e}")

        return False

    async def _fill_destination_link(self, page: Page, link: str) -> bool:
        """Fill the destination link (clickable URL) field on the pin builder."""
        if not link:
            return False

        locators = [
            page.locator('input[id="pin-draft-link"]'),
            page.locator('input[placeholder*="link" i]'),
            page.locator('input[placeholder*="website" i]'),
            page.locator('input[aria-label*="link" i]'),
            page.locator('input[name="link"]'),
        ]

        for loc in locators:
            try:
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.fill(link)
                    logger.info(f"Destination link filled: {link}")
                    return True
            except Exception:
                continue

        logger.warning("Could not fill destination link field")
        return False

    async def _extract_pin_from_page_state(self, page: Page) -> str | None:
        """Try to extract the new pin URL from Pinterest's client-side JS state."""
        try:
            pin_url = await page.evaluate("""
                () => {
                    // Check window.__PINTEREST_DATA__
                    if (window.__PINTEREST_DATA__) {
                        const data = window.__PINTEREST_DATA__;
                        if (data && data.resourceResponses) {
                            for (const resp of data.resourceResponses) {
                                if (resp.response && resp.response.data) {
                                    const pinData = resp.response.data;
                                    if (pinData.id) {
                                        return '/pin/' + pinData.id + '/';
                                    }
                                }
                            }
                        }
                    }

                    // Check React fiber state
                    const root = document.getElementById('root');
                    if (root && root._reactRootContainer) {
                        const state = root._reactRootContainer._internalRoot;
                        // Try to walk the fiber tree for pin data
                        // This is fragile but worth a try
                    }

                    // Check for any anchor tags with /pin/ that appeared recently
                    const pinLinks = document.querySelectorAll('a[href*="/pin/"]');
                    for (const link of pinLinks) {
                        const href = link.getAttribute('href');
                        if (href && /\\/pin\\/\\d+/.test(href)) {
                            return href;
                        }
                    }

                    return null;
                }
            """)
            if pin_url and "/pin/" in str(pin_url):
                if pin_url.startswith("http"):
                    return pin_url
                return f"https://www.pinterest.com{pin_url}"
        except Exception as e:
            logger.debug(f"Page state extraction failed: {e}")

        return None

    async def _find_newest_pin_on_profile(self, page: Page) -> str | None:
        """Navigate to user's pins page and find the most recently created pin."""
        try:
            username = await self._get_username(page)
            if not username:
                logger.warning("Cannot find profile pin URL: username unknown")
                return None

            await page.goto(f"https://www.pinterest.com/{username}/pins/", timeout=30000)
            await self._random_delay(3, 5)

            # Wait for pins to load
            await page.evaluate("window.scrollTo(0, 500)")
            await asyncio.sleep(2)

            # Extract first pin link (newest pin is typically shown first)
            pin_links = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a[href*="/pin/"]');
                    const urls = [];
                    for (const link of links) {
                        const href = link.getAttribute('href');
                        if (href) urls.push(href);
                    }
                    return urls;
                }
            """)

            if pin_links:
                for link in pin_links:
                    match = re.search(r'/pin/(\d+)', link)
                    if match:
                        pin_id = match.group(1)
                        url = f"https://www.pinterest.com/pin/{pin_id}/"
                        logger.info(f"Found newest pin on profile: {url}")
                        return url

            logger.warning("No pin links found on profile page")
            return None

        except Exception as e:
            logger.error(f"Profile pin lookup failed: {e}")
            return None

    # ── Engagement Scraping ────────────────────────────────

    async def scrape_pin_engagement(self, pin_url: str) -> EngagementData:
        page = await self._launch()

        try:
            await page.goto(pin_url, timeout=30000)
            await self._random_delay(3, 5)

            saves = 0
            clicks = 0

            try:
                save_count = page.locator('[data-test-id="pin-save-count"]')
                if await save_count.is_visible():
                    text = await save_count.text_content()
                    saves = int("".join(filter(str.isdigit, text or "0")))
            except Exception:
                pass

            try:
                click_count = page.locator('[data-test-id="pin-click-count"]')
                if await click_count.is_visible():
                    text = await click_count.text_content()
                    clicks = int("".join(filter(str.isdigit, text or "0")))
            except Exception:
                pass

            total = saves + clicks
            ctr = (clicks / total * 100) if total > 0 else 0.0
            save_rate = (saves / total * 100) if total > 0 else 0.0

            return EngagementData(impressions=0, saves=saves, clicks=clicks, ctr=ctr, save_rate=save_rate)

        except Exception as e:
            logger.error(f"Failed to scrape engagement from {pin_url}: {e}")
            return EngagementData()

    # ── Visibility Check ───────────────────────────────────

    async def check_pin_visibility(self, pin_title: str) -> bool:
        fresh_context = None
        temp_browser = None
        try:
            # Ensure playwright is started
            if self._playwright is None:
                await self._launch()
            
            # Use existing browser if available, otherwise launch a temporary one
            if self._browser:
                temp_browser = self._browser
                fresh_context = await temp_browser.new_context()
            else:
                # In persistent profile mode, we launch a separate temporary browser for incognito check
                temp_browser = await self._playwright.chromium.launch(headless=True)
                fresh_context = await temp_browser.new_context()

            fresh_page = await fresh_context.new_page()

            encoded_title = pin_title.replace(" ", "%20")
            await fresh_page.goto(
                f"https://www.pinterest.com/search/pins/?q={encoded_title}",
                timeout=30000
            )
            await self._random_delay(3, 5)

            content = await fresh_page.content()
            found = pin_title[:30] in content

            if found:
                logger.info(f"Pin '{pin_title}' found in search results")
            else:
                logger.warning(f"Pin '{pin_title}' NOT found in search results (possible shadowban)")

            return found

        except Exception as e:
            logger.error(f"Shadowban check failed: {e}")
            return True
        finally:
            if fresh_context:
                try:
                    await fresh_context.close()
                except Exception:
                    pass
            if temp_browser and temp_browser != self._browser:
                try:
                    await temp_browser.close()
                except Exception:
                    pass

    # ── Board Creation ─────────────────────────────────────

    async def create_board(self, name: str, description: str) -> bool:
        page = await self._launch()

        try:
            await page.goto("https://www.pinterest.com/create-board/", timeout=30000)
            await self._random_delay(2, 4)

            await page.fill('input[name="name"]', name)
            await self._random_delay(1, 2)

            desc_input = page.locator('textarea[name="description"]')
            if await desc_input.is_visible():
                await desc_input.fill(description)
                await self._random_delay(1, 2)

            create_btn = page.locator('button:has-text("Create")')
            await create_btn.click()
            await self._random_delay(3, 5)

            await self._save_session()
            logger.info(f"Board '{name}' created")
            return True

        except Exception as e:
            logger.error(f"Failed to create board '{name}': {e}")
            return False

    # ── Cleanup ────────────────────────────────────────────

    async def close(self) -> None:
        try:
            await self._save_session()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass