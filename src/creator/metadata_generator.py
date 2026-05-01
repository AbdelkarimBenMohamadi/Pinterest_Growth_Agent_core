import json
import logging
from src.models import ContentBrief, PinMetadata
from src.utils.config import get_groq_client, call_groq_with_retry, get_posting_config

logger = logging.getLogger(__name__)


def _build_description_link_text(destination_link: str) -> str:
    """Append a call-to-action link line to the description."""
    return f"\n\nShop now: {destination_link}"


async def generate_metadata(brief: ContentBrief, config: dict) -> PinMetadata:
    """
    Call Groq API to generate pin metadata. Uses OpenAI library with different base_url.
    """
    client = get_groq_client()
    model = config.get("ai", {}).get("text_model", "llama-3.3-70b-versatile")

    response_text = await call_groq_with_retry(
        client,
        model=model,
        messages=[
            {"role": "system", "content": "You are a Pinterest SEO expert. Return ONLY valid JSON."},
            {"role": "user", "content": f"""Generate Pinterest pin metadata for: "{brief.target_keyword}"
Related terms: {brief.related_terms}
Content type: {brief.content_type}

Return JSON with these exact keys:
- title: max 100 chars, keyword at start, click-worthy
- description: max 500 chars, natural language, end with 3-5 hashtags
- alt_text: max 500 chars, descriptive, keyword-rich
- suggested_board: best board name for this pin
- hashtags: list of 3-5 relevant hashtags"""}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=500,
    )

    data = json.loads(response_text)

    posting_config = get_posting_config(config)
    link_mode = posting_config.get("destination_link_mode", "none")
    destination_link = posting_config.get("default_destination_link", "")

    description = data["description"][:500]

    if link_mode in ("description_only", "both") and destination_link:
        description += _build_description_link_text(destination_link)

    return PinMetadata(
        title=data["title"][:100],
        description=description,
        alt_text=data["alt_text"][:500],
        suggested_board=data.get("suggested_board", ""),
        hashtags=data.get("hashtags", []),
        destination_link_mode=link_mode,
        default_destination_link=destination_link,
    )