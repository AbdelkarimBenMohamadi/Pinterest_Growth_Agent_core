import json
import logging
from src.models import ContentBrief, PinMetadata
from src.utils.config import get_groq_client, call_groq_with_retry

logger = logging.getLogger(__name__)


async def check_alignment(brief: ContentBrief, metadata: PinMetadata, image_prompt: str) -> bool:
    """
    Ask Groq: "Does this image prompt + metadata align with the keyword?"
    Returns True if aligned, False if not.

    This is a cheap text-only check — no vision API.
    """
    client = get_groq_client()

    response_text = await call_groq_with_retry(
        client,
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You check if content aligns with a keyword. Return ONLY JSON: {\"aligned\": true} or {\"aligned\": false}"},
            {"role": "user", "content": f"Keyword: {brief.target_keyword}\nImage prompt: {image_prompt}\nTitle: {metadata.title}\nDescription: {metadata.description}\n\nDoes this content match the keyword?"}
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=20,
    )

    data = json.loads(response_text)
    return data.get("aligned", False)