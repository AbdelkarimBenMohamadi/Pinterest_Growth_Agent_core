import logging
from src.models import ContentBrief, PinMetadata
from src.utils.config import call_text_ai_with_retry, get_text_ai_client
from src.utils.json_utils import parse_json_object

logger = logging.getLogger(__name__)


async def check_alignment(brief: ContentBrief, metadata: PinMetadata, image_prompt: str, config: dict) -> bool:
    """
    Ask the configured text provider whether image prompt + metadata align with the keyword.
    Returns True if aligned, False if not.

    This is a cheap text-only check — no vision API.
    """
    client, provider = get_text_ai_client(config)
    model = config.get("ai", {}).get("quality_gate_model") or config.get("ai", {}).get("text_model", "deepseek-v4-flash")

    logger.info("Running quality gate with %s/%s", provider, model)
    response_text = await call_text_ai_with_retry(
        client,
        provider,
        model=model,
        messages=[
            {"role": "system", "content": "You check if content aligns with a keyword. Return ONLY JSON: {\"aligned\": true} or {\"aligned\": false}"},
            {"role": "user", "content": f"Keyword: {brief.target_keyword}\nImage prompt: {image_prompt}\nTitle: {metadata.title}\nDescription: {metadata.description}\n\nDoes this content match the keyword?"}
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=80,
    )

    data = parse_json_object(response_text)
    return data.get("aligned", False)
