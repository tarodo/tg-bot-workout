import asyncio
from pathlib import Path

from ..config import get_settings
from ..logging import get_logger
from .base import Base, engine

logger = get_logger(__name__)
settings = get_settings()


async def init_db() -> None:
    """Initialize database."""
    try:
        # Create database directory if it doesn't exist
        db_path = Path(settings.DATA_DIR) / settings.DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Error initializing database", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
