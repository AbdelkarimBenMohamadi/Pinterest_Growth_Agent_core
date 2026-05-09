import asyncio

from src.models import Pin
from src.brain import seo_scraper, trend_monitor
from src.store.database import Database


def test_unverified_pin_is_not_marked_posted(tmp_path):
    db = Database(str(tmp_path / "pga.db"))
    db.initialize()

    pin_id = db.insert_pin(Pin(
        image_path="assets/example.png",
        image_hash="hash-1",
        title="Test Pin",
        description="Test description",
        target_keyword="web3",
        board_name="PGA Pins",
        status="pending",
    ))

    db.update_pin_posted(
        pin_id,
        "unverified",
        "https://www.pinterest.com/pin/123/",
        "post_unverified",
        {"pin_id": pin_id},
    )

    [pin] = db.get_recent_pins(days=1)

    assert pin.status == "unverified"
    assert pin.pinterest_url == "https://www.pinterest.com/pin/123/"
    assert pin.posted_at is None


async def _fake_safe_keywords(seed_keywords, db, config, page=None):
    assert page == "shared-page"
    return ["safe-keywords"]


async def _fake_safe_trends(categories, db, config, page=None):
    assert page == "shared-page"
    return ["safe-trends"]


async def _unexpected_fast(*args, **kwargs):
    raise AssertionError("fast scraper path should not run in GUI shared-page mode")


def test_gui_shared_page_overrides_fast_keyword_scraper(monkeypatch):
    monkeypatch.setattr(seo_scraper, "_scrape_keywords_safe", _fake_safe_keywords)
    monkeypatch.setattr(seo_scraper, "_extract_keywords_from_page", _unexpected_fast)

    result = asyncio.run(seo_scraper.scrape_keywords(
        ["web3"],
        db=None,
        config={"browser": {"mode": "gui"}, "scraper": {"mode": "fast"}},
        page="shared-page",
    ))

    assert result == ["safe-keywords"]


def test_gui_shared_page_overrides_fast_trend_scraper(monkeypatch):
    monkeypatch.setattr(trend_monitor, "_fetch_trends_safe", _fake_safe_trends)
    monkeypatch.setattr(trend_monitor, "_extract_trends_from_page", _unexpected_fast)

    result = asyncio.run(trend_monitor.fetch_trends(
        ["blockchain"],
        db=None,
        config={"browser": {"mode": "gui"}, "scraper": {"mode": "fast"}},
        page="shared-page",
    ))

    assert result == ["safe-trends"]
