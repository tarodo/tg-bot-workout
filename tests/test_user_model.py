from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.db.models import User


@pytest.mark.asyncio
async def test_user_creation(db_session: AsyncSession):
    """Test User model creation."""
    user = User(
        id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
        is_premium=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id == 123456789
    assert user.username == "test_user"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.language_code == "en"
    assert user.is_bot is False
    assert user.is_premium is False
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


@pytest.mark.asyncio
async def test_user_update(db_session: AsyncSession):
    """Test User model update."""
    # Create user
    user = User(
        id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
        is_premium=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Store original timestamps
    original_created_at = user.created_at
    original_updated_at = user.updated_at

    # Update user
    user.username = "updated_user"
    user.is_premium = True
    await db_session.commit()
    await db_session.refresh(user)

    # Check updates
    assert user.username == "updated_user"
    assert user.is_premium is True
    assert user.created_at == original_created_at  # Should not change
    assert user.updated_at > original_updated_at  # Should be updated


@pytest.mark.asyncio
async def test_user_repr(db_session: AsyncSession):
    """Test User model string representation."""
    user = User(
        id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
        is_premium=False,
    )

    assert str(user) == "<User 123456789 test_user>"
