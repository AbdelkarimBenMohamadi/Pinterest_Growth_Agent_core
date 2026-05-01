from datetime import datetime, timedelta, timezone as dt_timezone
import random
from src.models import DailyLimits
from src.utils.constants import DAILY_LIMITS


def get_daily_limits(account_created_at: datetime) -> DailyLimits:
    """
    Return limits based on account age from DAILY_LIMITS constant.
    """
    now = datetime.now(dt_timezone.utc)
    if account_created_at.tzinfo is None:
        account_created_at = account_created_at.replace(tzinfo=dt_timezone.utc)
    age_days = (now - account_created_at).days

    for (min_age, max_age), limits in DAILY_LIMITS.items():
        if min_age <= age_days <= max_age:
            return DailyLimits(**limits)

    return DailyLimits(**DAILY_LIMITS[(31, 9999)])


def distribute_posting_times(
    pin_count: int,
    peak_hours: list[int],
    timezone: str
) -> list[datetime]:
    """
    Distribute pin_count posting times across peak_hours.
    Add random 15-45 minute jitter between posts.
    Return sorted list of datetime objects.
    """
    import math
    now = datetime.now(dt_timezone.utc)
    times = []

    base_posts_per_hour = math.ceil(pin_count / len(peak_hours))
    remaining = pin_count

    for hour in peak_hours:
        if remaining <= 0:
            break
        posts_for_this_hour = min(base_posts_per_hour, remaining)
        for i in range(posts_for_this_hour):
            base_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if base_time <= now:
                base_time += timedelta(days=1)
            jitter_minutes = random.randint(15, 45)
            jitter_seconds = random.randint(0, 59)
            scheduled = base_time + timedelta(minutes=jitter_minutes, seconds=jitter_seconds)

            times.append(scheduled)
            remaining -= 1

    times.sort()
    return times[:pin_count]