import logging
from datetime import datetime, timedelta
from src.store.database import Database
from src.models import DailyLimits
from src.utils.constants import DAILY_LIMITS, HOURLY_POST_LIMIT, COOLDOWN_DEFAULT_HOURS

logger = logging.getLogger(__name__)


class SafetyManager:
    def __init__(self, db: Database, config: dict):
        self.db = db
        self.config = config
        self._action_count_today = 0
        self._posts_today = 0

    def check_daily_limits(self) -> bool:
        """Check if we can still post today. Returns True if safe."""
        from datetime import date
        today = date.today()

        conn = self.db._connect()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM pins WHERE status = 'posted' AND date(posted_at) = ?",
                (today.isoformat(),)
            )
            row = cursor.fetchone()
            self._posts_today = row[0] if row else 0

            cursor2 = conn.execute(
                """SELECT COUNT(*) as count FROM agent_log
                   WHERE action = 'post' AND date(created_at) = ?""",
                (today.isoformat(),)
            )
            row2 = cursor2.fetchone()
            self._action_count_today = row2[0] if row2 else 0
        finally:
            conn.close()

        created_date_str = self.config.get("account", {}).get("created_date", "2026-04-24")
        created_date = datetime.strptime(created_date_str, "%Y-%m-%d").replace(tzinfo=None)

        limits = self._get_limits_for_account_age(created_date)

        can_post = self._posts_today < limits.max_pins
        can_act = self._action_count_today < limits.max_actions

        if not can_post:
            logger.warning(f"Daily pin limit reached: {self._posts_today}/{limits.max_pins}")
        if not can_act:
            logger.warning(f"Daily action limit reached: {self._action_count_today}/{limits.max_actions}")

        return can_post and can_act

    def check_hourly_limits(self) -> bool:
        """Max 2 pins per hour. Returns True if safe."""
        from datetime import datetime, timedelta
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        conn = self.db._connect()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM pins WHERE status = 'posted' AND posted_at >= ?",
                (one_hour_ago,)
            )
            row = cursor.fetchone()
            recent_posts = row[0] if row else 0
        finally:
            conn.close()

        allowed = recent_posts < HOURLY_POST_LIMIT
        if not allowed:
            logger.warning(f"Hourly limit reached: {recent_posts}/{HOURLY_POST_LIMIT} posts in last hour")
        return allowed

    def enter_cooldown(self, hours: int = COOLDOWN_DEFAULT_HOURS) -> None:
        """Log cooldown start to DB."""
        from datetime import datetime, timedelta
        cooldown_until = datetime.utcnow() + timedelta(hours=hours)
        self.db.log_action("cooldown", {
            "cooldown_until": cooldown_until.isoformat(),
            "reason": "shadowban_detected"
        })
        logger.info(f"Entered cooldown until {cooldown_until}")

    def is_in_cooldown(self) -> bool:
        """Check if cooldown is active."""
        from datetime import datetime
        now = datetime.utcnow()

        conn = self.db._connect()
        try:
            cursor = conn.execute(
                """SELECT details FROM agent_log
                   WHERE action = 'cooldown'
                   ORDER BY created_at DESC LIMIT 1"""
            )
            row = cursor.fetchone()
            if not row:
                return False

            details = row[0]
            import json
            data = json.loads(details) if details else {}
            cooldown_until_str = data.get("cooldown_until", "")

            if not cooldown_until_str:
                return False

            cooldown_until = datetime.fromisoformat(cooldown_until_str)
            is_active = now < cooldown_until

            if is_active:
                logger.info(f"In cooldown until {cooldown_until}")
            return is_active

        finally:
            conn.close()

    def _get_limits_for_account_age(self, account_created_at: datetime) -> DailyLimits:
        """Internal helper to compute limits using DAILY_LIMITS constant."""
        from datetime import timezone
        age_days = (datetime.now(timezone.utc) - account_created_at.replace(tzinfo=timezone.utc)).days

        for (min_age, max_age), limits in DAILY_LIMITS.items():
            if min_age <= age_days <= max_age:
                return DailyLimits(**limits)

        return DailyLimits(**DAILY_LIMITS[(31, 9999)])