import pytest

from src.utils.config import get_browser_config, is_browser_headless


def test_get_browser_config_uses_mode():
    config = {"browser": {"mode": "headless", "session_file": "data/session.json"}}

    browser = get_browser_config(config)

    assert browser["mode"] == "headless"
    assert browser["headless"] is True
    assert is_browser_headless(config) is True


def test_get_browser_config_supports_legacy_headless():
    config = {"browser": {"headless": False}}

    browser = get_browser_config(config)

    assert browser["mode"] == "gui"
    assert browser["headless"] is False


def test_get_browser_config_rejects_invalid_mode():
    with pytest.raises(ValueError):
        get_browser_config({"browser": {"mode": "hidden"}})
