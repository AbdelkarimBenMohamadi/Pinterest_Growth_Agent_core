import json
import logging
from playwright.async_api import Page
from src.utils.config import get_groq_client, call_groq_with_retry

logger = logging.getLogger(__name__)


async def _get_interactive_elements(page: Page) -> str:
    """
    Extracts visible interactive elements from the page as JSON string.
    Used by self-healing to provide LLM with DOM context.
    """
    js_code = """
    async () => {
        const elements = [];
        const selectors = ['input', 'textarea', 'select', 'button', 'a', '[role="button"]', '[role="textbox"]', '[role="checkbox"]', '[role="radio"]'];
        
        for (const sel of selectors) {
            try {
                const els = document.querySelectorAll(sel);
                for (const el of els) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                            elements.push({
                                tag: el.tagName.toLowerCase(),
                                type: el.type || '',
                                name: el.name || '',
                                id: el.id || '',
                                className: el.className || '',
                                placeholder: el.placeholder || '',
                                ariaLabel: el.getAttribute('aria-label') || '',
                                text: el.innerText?.substring(0, 50) || '',
                                selector: ''
                            });
                        }
                    }
                }
            } catch(e) {}
        }
        
        // Generate unique selectors
        for (let i = 0; i < elements.length; i++) {
            const el = elements[i];
            if (el.id) {
                elements[i].selector = `#${el.id}`;
            } else if (el.name) {
                elements[i].selector = `${el.tag}[name="${el.name}"]`;
            } else if (el.className && typeof el.className === 'string') {
                const cls = el.className.split(' ')[0];
                if (cls) elements[i].selector = `${el.tag}.${cls}`;
            }
        }
        
        return JSON.stringify(elements.slice(0, 50));
    }
    """
    try:
        result = await page.evaluate(js_code)
        return result
    except Exception as e:
        logger.warning(f"Failed to extract interactive elements: {e}")
        return "[]"


async def heal_locator(
    page: Page,
    target_description: str,
    config: dict,
    page_context: str = "pin_creation_tool",
    db=None,
) -> str | None:
    """
    Uses Groq LLM to generate a Playwright CSS selector for a broken UI element
    by analyzing the current visible interactive DOM elements.
    Checks cached selectors first if db is provided.
    """
    if db:
        cached = db.get_cached_selector(page_context, target_description)
        if cached:
            logger.info(f"Using cached selector for '{target_description}': {cached}")
            return cached

    logger.info(f"Initiating self-healing for: '{target_description}'")

    dom_context = await _get_interactive_elements(page)
    if not dom_context or dom_context == "[]":
        logger.warning("Self-healing failed: No interactive elements found on the page.")
        return None

    client = get_groq_client()
    model = config.get("ai", {}).get("text_model", "llama-3.3-70b-versatile")

    prompt = f"""You are an expert Playwright automation engineer.
The standard locator for "{target_description}" on Pinterest just failed.

Here is a JSON list of all visible interactive elements currently on the page:
```json
{dom_context}
```

Identify the single element that most likely represents "{target_description}".
Return ONLY a valid Playwright CSS selector string that will uniquely match this element.
DO NOT wrap the response in code blocks, quotes, or JSON. Just return the raw selector string.
Example valid responses:
input[name="title"]
div[role="textbox"]
textarea[id="pin-draft-alttext"]
"""

    try:
        response_text = await call_groq_with_retry(
            client,
            model=model,
            messages=[
                {"role": "system", "content": "You are a specialized code generation tool. Output ONLY the raw CSS selector string requested. No explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Zero temperature for deterministic output
            max_tokens=100,
        )
        
        selector = response_text.strip().strip('`').strip('"').strip("'")
        
        # Basic validation to ensure it's not a hallucinated explanation
        if "\n" in selector or len(selector) > 150:
            logger.warning(f"Self-healing LLM returned an invalid selector format: {selector[:50]}...")
            return None
            
        logger.info(f"Self-healing LLM proposed new selector: {selector}")

        if db and selector:
            db.cache_selector(page_context, target_description, selector)

        return selector

    except Exception as e:
        logger.error(f"Self-healing LLM call failed: {e}")
        return None
