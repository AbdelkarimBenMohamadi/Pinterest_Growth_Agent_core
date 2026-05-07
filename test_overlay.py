import pytest
from src.creator.image_generator import _add_text_overlay

def test_add_text_overlay_disabled():
    image_bytes = b"fake_image_data"
    config = {"ai": {"text_overlay": {"enabled": False}}}
    result = _add_text_overlay(image_bytes, "Hello", config)
    assert result == image_bytes

def test_add_text_overlay_enabled_but_invalid_image():
    # Should handle exception and return original bytes
    image_bytes = b"not_an_image"
    config = {"ai": {"text_overlay": {"enabled": True}}}
    result = _add_text_overlay(image_bytes, "Hello", config)
    assert result == image_bytes
