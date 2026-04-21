import asyncio
import logging
import sys

# Add src to path so imports work when run directly
sys.path.insert(0, __file__.rsplit("/", 1)[0])

import config
from telegram_client import run


def setup_logging() -> None:
    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Quieten noisy telethon internals unless DEBUG
    if level > logging.DEBUG:
        logging.getLogger("telethon").setLevel(logging.WARNING)


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Telegram File Downloader")
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)
