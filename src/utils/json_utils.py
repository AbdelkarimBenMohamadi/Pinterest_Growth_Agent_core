import json
import re
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from strict JSON or a fenced/noisy model response."""
    if not text or not text.strip():
        raise ValueError("AI response was empty")

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        data = json.loads(cleaned[start:end + 1])

    if not isinstance(data, dict):
        raise ValueError("AI response JSON was not an object")

    return data
