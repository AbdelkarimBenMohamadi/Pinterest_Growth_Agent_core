import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.worker.scheduler import get_daily_limits, distribute_posting_times
from src.models import DailyLimits


def test_daily_limits_age_0_to_7():
    recent = datetime.now(timezone.utc) - timedelta(days=3)
    limits = get_daily_limits(recent)
    assert limits.max_pins == 1
    assert limits.max_actions == 10


def test_daily_limits_age_8_to_14():
    age_10 = datetime.now(timezone.utc) - timedelta(days=10)
    limits = get_daily_limits(age_10)
    assert limits.max_pins == 2
    assert limits.max_actions == 20


def test_daily_limits_age_15_to_30():
    age_20 = datetime.now(timezone.utc) - timedelta(days=20)
    limits = get_daily_limits(age_20)
    assert limits.max_pins == 5
    assert limits.max_actions == 40


def test_daily_limits_age_31_plus():
    old = datetime.now(timezone.utc) - timedelta(days=60)
    limits = get_daily_limits(old)
    assert limits.max_pins == 8
    assert limits.max_actions == 60


def test_distribute_posting_times_count():
    times = distribute_posting_times(5, [10, 14, 18, 20], "US/Eastern")
    assert len(times) == 5


def test_distribute_posting_times_sorted():
    times = distribute_posting_times(4, [10, 14], "US/Eastern")
    assert times == sorted(times)


def test_distribute_posting_times_in_future():
    now = datetime.now(timezone.utc)
    times = distribute_posting_times(3, [23], "US/Eastern")
    for t in times:
        assert t > now