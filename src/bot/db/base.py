import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from ..config import get_settings

settings = get_settings()

# Create data directory if it doesn't exist
os.makedirs(settings.DATA_DIR, exist_ok=True)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Set to False in production
    future=True,
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session() as session:
        yield session
