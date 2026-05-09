import os
import yaml
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError

load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_COMPATIBLE_TEXT_PROVIDERS = {
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
    },
    "groq": {
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
    },
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
    },
    "openrouter": {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
    },
}

REQUIRED_CONFIG_KEYS = [
    "account.created_date",
    "niche.seed_keywords",
    "schedule.peak_hours",
    "ai.text_model",
    "paths.database",
]

VALID_BROWSER_MODES = {"gui", "headless"}


def load_config(config_path: str = "config.yaml") -> dict:
    """Load config.yaml and merge with environment variables."""
    load_dotenv()

    config_file = Path(config_path)
    if not config_file.exists():
        logger.warning(f"config.yaml not found at {config_path}")
        return {}

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _apply_env_overrides(config)
    _validate_required_keys(config)

    return config


def _apply_env_overrides(config: dict) -> None:
    """Override config values with environment variables where set."""
    if os.getenv("GROQ_API_KEY"):
        config.setdefault("ai", {})["groq_api_key"] = os.getenv("GROQ_API_KEY")
    if os.getenv("DEEPSEEK_API_KEY"):
        config.setdefault("ai", {})["deepseek_api_key"] = os.getenv("DEEPSEEK_API_KEY")
    if os.getenv("OPENAI_API_KEY"):
        config.setdefault("ai", {})["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("OPENROUTER_API_KEY"):
        config.setdefault("ai", {})["openrouter_api_key"] = os.getenv("OPENROUTER_API_KEY")
    if os.getenv("PROXY_URL"):
        config.setdefault("safety", {})["proxy_url"] = os.getenv("PROXY_URL")
    if os.getenv("TOGETHER_API_KEY"):
        config.setdefault("ai", {})["together_api_key"] = os.getenv("TOGETHER_API_KEY")
    if os.getenv("HF_API_KEY"):
        config.setdefault("ai", {})["huggingface_api_key"] = os.getenv("HF_API_KEY")
    if os.getenv("PGA_BROWSER_MODE"):
        config.setdefault("browser", {})["mode"] = os.getenv("PGA_BROWSER_MODE")


def _validate_required_keys(config: dict) -> None:
    """Raise ValueError if required keys are missing."""
    for key_path in REQUIRED_CONFIG_KEYS:
        parts = key_path.split(".")
        value = config
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                raise ValueError(f"Missing required config key: {key_path}")
            value = value[part]


VALID_LINK_MODES = {"none", "description_only", "destination_link", "both"}


def get_posting_config(config: dict) -> dict:
    """Return the posting config dict with validated link mode."""
    posting = config.get("posting", {})
    link_mode = posting.get("destination_link_mode", "none")
    if link_mode not in VALID_LINK_MODES:
        raise ValueError(
            f"Invalid destination_link_mode: '{link_mode}'. "
            f"Must be one of: {', '.join(sorted(VALID_LINK_MODES))}"
        )
    return posting


def get_browser_config(config: dict) -> dict:
    """Return browser config with roadmap-level browser.mode resolved."""
    browser = config.get("browser", {})
    mode = browser.get("mode")

    if mode is None:
        legacy_headless = browser.get("headless", False)
        mode = "headless" if legacy_headless else "gui"
        logger.warning(
            "browser.headless is deprecated. Use browser.mode: %s instead.",
            mode,
        )

    if mode not in VALID_BROWSER_MODES:
        raise ValueError(
            f"Invalid browser.mode: '{mode}'. Must be one of: "
            f"{', '.join(sorted(VALID_BROWSER_MODES))}"
        )

    return {
        "mode": mode,
        "headless": mode == "headless",
        "session_file": browser.get("session_file", "data/pinterest_session.json"),
        "chrome_profile_path": browser.get("chrome_profile_path", ""),
    }


def is_browser_headless(config: dict) -> bool:
    """Return True when browser.mode resolves to headless."""
    return get_browser_config(config)["headless"]


def get_groq_api_key() -> str:
    """Get GROQ_API_KEY from environment. Raises ValueError if missing."""
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not set in .env")
    return key


def get_openai_api_key() -> str:
    """Get OPENAI_API_KEY from environment. Raises ValueError if missing."""
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY not set in .env")
    return key


def get_deepseek_api_key() -> str:
    """Get DEEPSEEK_API_KEY from environment. Raises ValueError if missing."""
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY not set in .env")
    return key


def get_pinterest_credentials() -> tuple[str, str]:
    """Return (email, password) from environment. Raises ValueError if missing."""
    email = os.getenv("PINTEREST_EMAIL", "")
    password = os.getenv("PINTEREST_PASSWORD", "")
    if not email or not password:
        raise ValueError("PINTEREST_EMAIL and PINTEREST_PASSWORD must be set in .env")
    return email, password


def get_together_api_key() -> str:
    """Get TOGETHER_API_KEY from environment. Returns empty string if not set."""
    return os.getenv("TOGETHER_API_KEY", "")


def get_huggingface_api_key() -> str:
    """Get HF_API_KEY from environment. Returns empty string if not set."""
    return os.getenv("HF_API_KEY", "")


def get_groq_client() -> AsyncOpenAI:
    """Create Groq client. Reuse this in metadata_generator and quality_gate."""
    return AsyncOpenAI(
        api_key=get_groq_api_key(),
        base_url="https://api.groq.com/openai/v1"
    )


def get_text_ai_client(config: dict) -> tuple[AsyncOpenAI, str]:
    """Create an OpenAI-compatible text client from ai.text_provider."""
    provider = config.get("ai", {}).get("text_provider", "groq").lower().strip()
    provider_cfg = OPENAI_COMPATIBLE_TEXT_PROVIDERS.get(provider)
    if not provider_cfg:
        raise ValueError(
            f"Unsupported ai.text_provider '{provider}'. "
            f"Use one of: {', '.join(sorted(OPENAI_COMPATIBLE_TEXT_PROVIDERS))}"
        )

    api_key_env = provider_cfg["api_key_env"]
    api_key = os.getenv(api_key_env, "")
    if not api_key:
        raise ValueError(f"{api_key_env} not set in .env")

    return AsyncOpenAI(api_key=api_key, base_url=provider_cfg["base_url"]), provider


async def call_groq_with_retry(
    client: AsyncOpenAI,
    max_retries: int = 3,
    **kwargs
) -> str:
    """
    Call Groq chat completion with exponential backoff.
    Returns the response content string.

    Handles:
    - 429 Rate Limit: wait 2^attempt seconds, retry
    - Timeout: retry immediately
    - Connection error: retry after 5s
    - Other errors: raise immediately
    """
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if not content:
                raise ValueError("AI provider returned an empty response")
            return content
        except RateLimitError:
            wait = 2 ** (attempt + 1)
            logger.warning(f"Groq rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(wait)
        except APITimeoutError:
            logger.warning(f"Groq timeout (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(1)
        except APIConnectionError:
            logger.warning(f"Groq connection error. Waiting 5s (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(5)

    raise Exception(f"Groq API failed after {max_retries} retries")


async def call_text_ai_with_retry(
    client: AsyncOpenAI,
    provider: str,
    max_retries: int = 3,
    **kwargs
) -> str:
    """Call an OpenAI-compatible text provider with basic retry handling."""
    provider_label = provider.title()
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if not content:
                raise ValueError("AI provider returned an empty response")
            return content
        except RateLimitError:
            wait = 2 ** (attempt + 1)
            logger.warning(f"{provider_label} rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(wait)
        except APITimeoutError:
            logger.warning(f"{provider_label} timeout (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(1)
        except APIConnectionError:
            logger.warning(f"{provider_label} connection error. Waiting 5s (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(5)
        except ValueError as e:
            if "empty response" not in str(e).lower():
                raise
            logger.warning(f"{provider_label} returned an empty response (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(1)

    raise Exception(f"{provider_label} API failed after {max_retries} retries")
