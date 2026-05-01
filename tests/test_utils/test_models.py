import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_models_import():
    from src.models import Keyword, Pin, Trend, EngagementData, ContentBrief, PinMetadata, DailyLimits
    assert Keyword is not None
    assert Pin is not None
    assert Trend is not None
    assert EngagementData is not None


def test_keyword_dataclass():
    from src.models import Keyword
    kw = Keyword(term="test keyword", suggestion_rank=1, related_terms=["a", "b"])
    assert kw.term == "test keyword"
    assert kw.suggestion_rank == 1
    assert kw.related_terms == ["a", "b"]


def test_pin_dataclass():
    from src.models import Pin
    pin = Pin(title="Test Pin", target_keyword="test kw", image_path="/path/to/img.png", image_hash="abc123")
    assert pin.title == "Test Pin"
    assert pin.status == "pending"