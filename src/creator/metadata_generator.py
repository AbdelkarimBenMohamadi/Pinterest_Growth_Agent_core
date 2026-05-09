import logging
from src.models import ContentBrief, PinMetadata
from src.utils.config import call_text_ai_with_retry, get_posting_config, get_text_ai_client
from src.utils.json_utils import parse_json_object

logger = logging.getLogger(__name__)


def _build_description_link_text(destination_link: str) -> str:
    """Append a call-to-action link line to the description."""
    return f"\n\nShop now: {destination_link}"


async def generate_metadata(brief: ContentBrief, config: dict) -> PinMetadata:
    """
    Call the configured OpenAI-compatible text provider to generate pin metadata.
    """
    client, provider = get_text_ai_client(config)
    model = config.get("ai", {}).get("text_model", "deepseek-v4-flash")

    logger.info("Generating metadata with %s/%s", provider, model)
    response_text = await call_text_ai_with_retry(
        client,
        provider,
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

    data = parse_json_object(response_text)

    posting_config = get_posting_config(config)
    link_mode = posting_config.get("destination_link_mode", "none")
    destination_link = posting_config.get("default_destination_link", "")

    description = data["description"][:500]

    if link_mode in ("description_only", "both") and destination_link:
        description += _build_description_link_text(destination_link)

    hashtags = data.get("hashtags", [])
    if isinstance(hashtags, str):
        hashtags = [tag.strip() for tag in hashtags.replace(",", " ").split() if tag.strip()]
    if not isinstance(hashtags, list):
        hashtags = []

    return PinMetadata(
        title=data["title"][:100],
        description=description,
        alt_text=data["alt_text"][:500],
        suggested_board=data.get("suggested_board", ""),
        hashtags=hashtags[:5],
        destination_link_mode=link_mode,
        default_destination_link=destination_link,
    )
