import pytest

from src.creator import image_generator


@pytest.mark.asyncio
async def test_openai_image_provider_uses_openai_first(monkeypatch):
    calls = []

    async def fake_openai(prompt, config):
        calls.append("openai")
        return b"openai-image"

    monkeypatch.setattr(image_generator, "_openai_images_generate", fake_openai)

    result = await image_generator._generate_with_provider_chain(
        "openai",
        "test prompt",
        {"ai": {}},
    )

    assert result == b"openai-image"
    assert calls == ["openai"]


@pytest.mark.asyncio
async def test_openai_image_provider_falls_back_to_pollinations(monkeypatch):
    calls = []

    async def fake_openai(prompt, config):
        calls.append("openai")
        raise ValueError("missing key")

    async def fake_pollinations(prompt, negative=""):
        calls.append("pollinations")
        return b"pollinations-image"

    monkeypatch.setattr(image_generator, "_openai_images_generate", fake_openai)
    monkeypatch.setattr(image_generator, "_pollinations_generate", fake_pollinations)

    result = await image_generator._generate_with_provider_chain(
        "openai_images",
        "test prompt",
        {"ai": {}},
    )

    assert result == b"pollinations-image"
    assert calls == ["openai", "pollinations"]
