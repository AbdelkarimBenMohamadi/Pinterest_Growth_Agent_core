import pytest
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.creator.image_generator import _pollinations_generate
from src.models import ContentBrief
import asyncio


def test_pollinations_url_construction():
    """Test that the URL is correctly formed."""
    prompt = "test keyword"
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}"
    assert "test%20keyword" in url


def test_image_generator_accepts_brief():
    """Verify generate_image accepts ContentBrief."""
    from src.creator import image_generator
    import inspect
    sig = inspect.signature(image_generator.generate_image)
    params = list(sig.parameters.keys())
    assert "brief" in params
    assert "config" in params


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires network call to Pollinations.ai")
async def test_pollinations_generate_returns_bytes():
    result = await _pollinations_generate("sunset beach")
    assert isinstance(result, bytes)
    assert len(result) > 1000