"""
Diagnostic Agent — AI-powered scraper health monitoring and self-healing.

Watches scraper health metrics and triggers AI diagnosis when failure thresholds are hit.
Reports to dashboard instead of auto-applying fixes.
"""
import asyncio
import json
import logging
from datetime import datetime
from dataclasses import dataclass
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from src.utils.config import get_groq_client, call_groq_with_retry
from src.store.database import Database
from src.utils.constants import SESSION_FILE, DIAGNOSTIC_CONSECUTIVE_FAILURES, DIAGNOSTIC_AVG_RESULTS_THRESHOLD

logger = logging.getLogger(__name__)

DIAGNOSTIC_SYSTEM_PROMPT = """You are a Pinterest Growth Agent diagnostic expert. Your job is to diagnose why a scraper module is failing or returning poor results.

You have access to the live Pinterest website. Your output is a JSON diagnostic report — NEVER actual code.

For each diagnosis, provide:
1. ROOT CAUSE — What specifically is broken? Be specific (selector names, API endpoint changes, etc.)
2. SEVERITY — "critical" | "moderate" | "low"
3. SUGGESTED_FIX — A clear description of what needs to change. Be concrete, name specific selectors, API endpoints, or logic changes.
4. ALTERNATIVE_APPROACH — What to do if the fix doesn't work (e.g., use different page, different selector, etc.)

Format your final answer as a JSON object with keys: root_cause, severity, suggested_fix, alternative_approach

IMPORTANT: 
- Do NOT suggest deleting files or large rewrites — be surgical
- Do NOT return Python code — just diagnostic text
- If the issue is a Pinterest DOM change, specify the exact CSS selector or XPath that needs updating
- If the issue is an API change, specify the new endpoint pattern
"""


@dataclass
class ScrapResult:
    module: str
    success: bool
    result_count: int
    error: str | None
    scraped_content: str | None


async def diagnose_with_ai(module: str, last_error: str, recent_results: list[dict], scraped_sample: str | None = None) -> dict:
    """Use Groq LLM to diagnose the scraper failure and propose a fix."""
    client = get_groq_client()

    health_summary = "\n".join([
        f"Run #{r['run_count']}: success={bool(r['success_count'])}, "
        f"failure_count={r['failure_count']}, avg_results={r['avg_results']:.1f}, "
        f"last_error={r['last_error'] or 'none'}"
        for r in recent_results
    ])

    prompt = f"""## Scraper Module: {module}

### Last Error:
{last_error}

### Recent Run History:
{health_summary}

### Live Page Sample (first 500 chars of what the scraper sees):
{scraped_sample or 'No sample captured'}

---

{DIAGNOSTIC_SYSTEM_PROMPT}

Return your diagnosis as a JSON object with root_cause, severity, suggested_fix, and alternative_approach keys."""

    try:
        response = await call_groq_with_retry(
            client,
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a diagnostic expert. Return ONLY a JSON object with no markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        result = json.loads(response.strip())
        logger.info(f"AI diagnosis for {module}: {result.get('root_cause', 'unknown')[:80]}")
        return result
    except Exception as e:
        logger.error(f"Groq diagnosis failed: {e}")
        return {
            "root_cause": f"Groq API error: {e}",
            "severity": "moderate",
            "suggested_fix": "Manual inspection required. Groq API failed.",
            "alternative_approach": "Check .env GROQ_API_KEY and internet connection."
        }


async def inspect_live_page(module: str, config: dict) -> str | None:
    """Capture live page content from Pinterest to feed to AI for diagnosis."""
    from pathlib import Path
    SESSION_FILE = Path("data/pinterest_session.json")

    urls = {
        "seo_scraper": "https://www.pinterest.com/search/pins/?q=home+decor",
        "trend_monitor": "https://www.pinterest.com/search/pins/?q=interior+design",
    }
    url = urls.get(module)
    if not url:
        return None

    stealth = Stealth()
    sample_lines = []

    try:
        async with stealth.use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            context = None
            try:
                storage = str(SESSION_FILE) if SESSION_FILE.exists() else None
                context = await browser.new_context(
                    storage_state=storage,
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    locale="en-US",
                )
                page = await context.new_page()

                # Capture API responses
                async def on_response(response):
                    if "AdvancedTypeahead" in response.url:
                        try:
                            data = await response.json()
                            items = data.get("resource_response", {}).get("data", {}).get("items", [])
                            for item in items:
                                if isinstance(item, dict) and "query" in item:
                                    sample_lines.append(f"API suggestion: {item['query']}")
                        except Exception as e:
                            logger.debug(f"Diagnostic API parse failed: {e}")

                page.on("response", on_response)

                await page.goto(url, timeout=30000)
                await asyncio.sleep(4)

                # Try typing to trigger autocomplete
                try:
                    search = page.locator('input[data-test-id="search-box-input"]').first
                    if await search.count() > 0:
                        await search.click()
                        await asyncio.sleep(0.5)
                        await search.fill("")
                        for char in "home":
                            await page.keyboard.press(char)
                            await asyncio.sleep(0.08)
                        await asyncio.sleep(2)
                except Exception:
                    pass

                # Get page text
                text = await page.inner_text("body")
                sample_lines.append(f"Page text (500 chars): {text[:500]}")

                # Get headings
                headings = await page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('h2, h3')).slice(0, 10).map(h => h.textContent?.trim());
                }""")
                if headings:
                    sample_lines.append(f"Headings: {headings}")
            finally:
                # Guaranteed cleanup of context and browser
                if context:
                    try:
                        await context.close()
                    except Exception:
                        pass
                try:
                    await browser.close()
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Live inspection failed for {module}: {e}")
        return None

    return "\n".join(sample_lines[:30])


async def check_scraper_health(db: Database) -> list[dict]:
    """Check all scraper health records and trigger diagnostics for unhealthy modules."""
    health_records = db.get_scraper_health()
    triggered = []

    for record in health_records:
        module = record["module_name"]
        failure_count = record["failure_count"] or 0
        avg_results = record["avg_results"] or 0.0

        if failure_count >= THRESHOLD_CONSECUTIVE_FAILURES:
            logger.warning(f"Scraper '{module}' has {failure_count} consecutive failures. Triggering diagnosis.")
            triggered.append((module, "consecutive_failures", record))
        elif avg_results > 0 and avg_results < DIAGNOSTIC_AVG_RESULTS_THRESHOLD:
            logger.warning(f"Scraper '{module}' avg results {avg_results:.1f} below threshold. Triggering diagnosis.")
            triggered.append((module, "low_avg_results", record))

    return triggered


async def run_diagnostic(module: str, trigger_reason: str, health_record: dict, config: dict, db: Database) -> dict:
    """Run a full diagnostic cycle for a single scraper."""
    last_error = health_record.get("last_error", "Unknown error")

    # Inspect live page
    scraped_sample = await inspect_live_page(module, config)

    # Run AI diagnosis (pass the existing health_record instead of re-querying)
    diagnosis = await diagnose_with_ai(module, last_error, [health_record], scraped_sample)

    # Store diagnostic report
    report_id = db.insert_diagnostic_report(
        module_name=module,
        failure_count=health_record.get("failure_count", 0),
        last_error=last_error,
        diagnosis=diagnosis.get("root_cause", "Unknown"),
        suggested_fix=diagnosis.get("suggested_fix", ""),
    )

    db.log_action("diagnostic_run", {
        "module": module,
        "trigger_reason": trigger_reason,
        "diagnosis": diagnosis.get("root_cause"),
        "severity": diagnosis.get("severity"),
        "report_id": report_id,
    })

    logger.info(f"Diagnostic report #{report_id} created for '{module}' — {diagnosis.get('severity', 'unknown')} severity")

    return diagnosis


async def run_all_diagnostics(config: dict, db: Database) -> list[dict]:
    """Check all scrapers and run diagnostics on any unhealthy ones."""
    unhealthy = await check_scraper_health(db)
    results = []

    for module, reason, record in unhealthy:
        try:
            diag = await run_diagnostic(module, reason, record, config, db)
            results.append({"module": module, "reason": reason, "diagnosis": diag})
        except Exception as e:
            logger.error(f"Diagnostic run failed for '{module}': {e}")

    return results


async def diagnose_on_demand(module: str, config: dict, db: Database) -> dict:
    """Manually trigger a diagnostic for a specific module (called from dashboard or CLI)."""
    health = db.get_scraper_health()
    record = next((r for r in health if r["module_name"] == module), None)

    if not record:
        record = {
            "module_name": module,
            "failure_count": 1,
            "last_error": "Manually triggered",
            "avg_results": 0.0,
        }

    return await run_diagnostic(module, "manual_trigger", record, config, db)