from datetime import datetime, timedelta, timezone

import pytest

from src.worker.scheduler import distribute_posting_times, wait_until_scheduled


def test_distribute_posting_times_returns_utc_datetimes():
    scheduled = distribute_posting_times(
        pin_count=3,
        peak_hours=[10, 14],
        timezone="US/Eastern",
        interval_min_minutes=0,
        interval_max_minutes=0,
    )

    assert len(scheduled) == 3
    assert scheduled == sorted(scheduled)
    assert all(item.tzinfo == timezone.utc for item in scheduled)


def test_distribute_posting_times_handles_empty_inputs():
    assert distribute_posting_times(0, [10], "UTC") == []
    assert distribute_posting_times(3, [], "UTC") == []


@pytest.mark.asyncio
async def test_wait_until_scheduled_returns_immediately_for_past_time():
    past = datetime.now(timezone.utc) - timedelta(seconds=1)

    await wait_until_scheduled(past)
