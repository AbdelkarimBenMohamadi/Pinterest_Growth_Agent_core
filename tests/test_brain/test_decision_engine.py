import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.brain.decision_engine import select_todays_content
from src.models import Keyword, Trend


def test_seo_trend_split():
    keywords = [Keyword(term=f"kw{i}", suggestion_rank=i) for i in range(10)]
    trends = [Trend(name=f"trend{i}", velocity=1.5) for i in range(5)]
    briefs = select_todays_content(keywords, trends, daily_pin_limit=10, seo_percent=70)
    
    seo = sum(1 for b in briefs if b.content_type == "seo")
    trend = sum(1 for b in briefs if b.content_type == "trend")
    
    assert seo == 7, f"Expected 7 SEO briefs, got {seo}"
    assert trend == 3, f"Expected 3 trend briefs, got {trend}"


def test_keyword_priority():
    keywords = [
        Keyword(term="high perf", suggestion_rank=5, performance_score=3.0),
        Keyword(term="low perf", suggestion_rank=1, performance_score=0.5),
    ]
    trends = []
    briefs = select_todays_content(keywords, trends, daily_pin_limit=2, seo_percent=100)
    
    assert briefs[0].target_keyword == "high perf"
    assert briefs[1].target_keyword == "low perf"


def test_trend_velocity_filter():
    keywords = []
    trends = [
        Trend(name="rising", velocity=2.0),
        Trend(name="declining", velocity=0.5),
        Trend(name="neutral", velocity=1.0),
    ]
    briefs = select_todays_content(keywords, trends, daily_pin_limit=3, seo_percent=0)
    
    trend_names = [b.target_keyword for b in briefs if b.content_type == "trend"]
    assert "rising" in trend_names
    assert "declining" not in trend_names
    assert "neutral" not in trend_names


def test_empty_inputs():
    briefs = select_todays_content([], [], daily_pin_limit=5, seo_percent=70)
    assert len(briefs) == 0