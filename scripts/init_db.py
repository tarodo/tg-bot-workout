#!/usr/bin/env python
import asyncio
import sys
from pathlib import Path

from bot.db.init_db import init_db
from bot.logging import get_logger, setup_logging

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))


logger = get_logger(__name__)


async def main() -> None:
    """Initialize database."""
    try:
        setup_logging()
        await init_db()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
