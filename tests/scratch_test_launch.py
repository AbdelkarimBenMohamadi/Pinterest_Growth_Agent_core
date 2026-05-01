import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.worker.pinterest_client import PinterestClient
from src.utils.config import load_config
from src.utils.logger import setup_logging

async def test_launch():
    setup_logging()
    logger = logging.getLogger("test_launch")
    
    config = load_config()
    client = PinterestClient(config)
    
    logger.info("Testing browser launch with persistent profile...")
    try:
        page = await client._launch()
        logger.info(f"Successfully launched browser. Current URL: {page.url}")
        
        # Wait a bit to see the browser (if headful)
        await asyncio.sleep(5)
        
        await client.close()
        logger.info("Browser closed successfully.")
    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")

if __name__ == "__main__":
    asyncio.run(test_launch())
