from collections.abc import AsyncGenerator

import pytest
from bot.db.init_db import init_db
from bot.db.models.base import Base
from bot.db.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
async def setup_database() -> AsyncGenerator[None, None]:
    """Set up test database."""
    # Use in-memory SQLite for tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as _:
        await init_db()
        yield

    await engine.dispose()


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    # Create tables for each test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def user_repo(db_session: AsyncSession) -> UserRepository:
    """Create a UserRepository instance for each test."""
    return UserRepository(db_session)
