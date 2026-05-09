import asyncio
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
import random
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from src.models import DailyLimits
from src.utils.constants import DAILY_LIMITS

logger = logging.getLogger(__name__)


def get_daily_limits(account_created_at: datetime) -> DailyLimits:
    """
    Return limits based on account age from DAILY_LIMITS constant.
    """
    now = datetime.now(dt_timezone.utc)
    if account_created_at.tzinfo is None:
        account_created_at = account_created_at.replace(tzinfo=dt_timezone.utc)
    age_days = (now - account_created_at).days
    if age_days < 0:
        logger.warning("Account created date is in the future. Treating account age as 0 days.")
        age_days = 0

    for (min_age, max_age), limits in DAILY_LIMITS.items():
        if min_age <= age_days <= max_age:
            return DailyLimits(**limits)

    return DailyLimits(**DAILY_LIMITS[(31, 9999)])


def distribute_posting_times(
    pin_count: int,
    peak_hours: list[int],
    timezone: str,
    interval_min_minutes: int = 15,
    interval_max_minutes: int = 45,
) -> list[datetime]:
    """
    Distribute pin_count posting times across peak_hours.
    Add random jitter between posts.
    Return sorted UTC datetime objects.
    """
    import math

    if pin_count <= 0 or not peak_hours:
        return []

    try:
        local_tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        logger.warning("Unknown timezone '%s'. Falling back to UTC.", timezone)
        local_tz = dt_timezone.utc

    now_local = datetime.now(local_tz)
    min_minutes = max(0, int(interval_min_minutes))
    max_minutes = max(min_minutes, int(interval_max_minutes))
    times = []

    base_posts_per_hour = math.ceil(pin_count / len(peak_hours))
    remaining = pin_count

    for hour in peak_hours:
        if remaining <= 0:
            break
        posts_for_this_hour = min(base_posts_per_hour, remaining)
        for i in range(posts_for_this_hour):
            base_time = now_local.replace(hour=hour, minute=0, second=0, microsecond=0)
            if base_time <= now_local:
                base_time += timedelta(days=1)
            jitter_minutes = random.randint(min_minutes, max_minutes)
            jitter_seconds = random.randint(0, 59)
            scheduled = base_time + timedelta(minutes=jitter_minutes, seconds=jitter_seconds)

            times.append(scheduled.astimezone(dt_timezone.utc))
            remaining -= 1

    times.sort()
    return times[:pin_count]


async def wait_until_scheduled(scheduled_dt: datetime | None) -> None:
    """Wait until scheduled_dt, if it is in the future."""
    if not scheduled_dt:
        return

    if scheduled_dt.tzinfo is None:
        scheduled_dt = scheduled_dt.replace(tzinfo=dt_timezone.utc)

    now = datetime.now(dt_timezone.utc)
    delay = (scheduled_dt.astimezone(dt_timezone.utc) - now).total_seconds()

    if delay > 0:
        logger.info("Waiting %.0f seconds until scheduled post time %s", delay, scheduled_dt.isoformat())
        await asyncio.sleep(delay)
