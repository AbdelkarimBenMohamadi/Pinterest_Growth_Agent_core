import logging
from src.worker.pinterest_client import PinterestClient
from src.models import Pin, EngagementData
from src.store.database import Database

logger = logging.getLogger(__name__)


async def scrape_engagement(
    client: PinterestClient,
    pins: list[Pin],
    db: Database
) -> list[EngagementData]:
    """
    For each pin with a pinterest_url, scrape engagement metrics.
    Store results in DB. Return list of EngagementData.
    """
    results: list[EngagementData] = []

    for pin in pins:
        if not pin.pinterest_url:
            continue

        try:
            if client._context is None or client._browser is None:
                await client._launch()
            engagement = await client.scrape_pin_engagement(pin.pinterest_url)
            engagement.pin_id = pin.id
            db.insert_engagement(engagement)
            results.append(engagement)
            logger.info(f"Scraped engagement for pin {pin.id}: saves={engagement.saves}, clicks={engagement.clicks}")
        except Exception as e:
            logger.warning(f"Failed to scrape engagement for pin {pin.id}: {e}")
            continue

    return results