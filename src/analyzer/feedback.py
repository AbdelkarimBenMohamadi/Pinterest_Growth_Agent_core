import logging
from src.models import EngagementData
from src.store.database import Database

logger = logging.getLogger(__name__)


def update_keyword_scores(engagement_data: list[EngagementData], db: Database) -> None:
    """
    Update keyword performance scores:
    - save_rate > 1%  → boost score +2.0
    - ctr > 1.5%      → boost score +1.0
    - zero engagement → penalty -0.5
    """
    # Fetch all recent pins ONCE and build lookup dict (avoids N+1 query)
    pins_result = db.get_recent_pins(days=7)
    pin_lookup: dict[int, object] = {p.id: p for p in pins_result}

    for data in engagement_data:
        pin = pin_lookup.get(data.pin_id)
        if not pin:
            continue

        if data.save_rate > 1.0:
            db.update_keyword_score(pin.target_keyword, 2.0)
            logger.info(f"Keyword '{pin.target_keyword}' boosted: high save_rate {data.save_rate:.2f}%")

        elif data.ctr > 1.5:
            db.update_keyword_score(pin.target_keyword, 1.0)
            logger.info(f"Keyword '{pin.target_keyword}' boosted: high CTR {data.ctr:.2f}%")

        elif data.impressions == 0 and data.saves == 0 and data.clicks == 0:
            db.update_keyword_score(pin.target_keyword, -0.5)
            logger.warning(f"Keyword '{pin.target_keyword}' penalized: zero engagement")