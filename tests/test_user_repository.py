from datetime import datetime

import pytest


@pytest.mark.asyncio
async def test_create_user(user_repo):
    """Test creating a new user."""
    user = await user_repo.create_user(
        user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
    )

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
async def test_get_user(user_repo):
    """Test getting an existing user."""
    # Create user first
    created_user = await user_repo.create_user(
        user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
    )

    # Get user
    user = await user_repo.get_user(123456789)

    assert user is not None
    assert user.id == created_user.id
    assert user.username == created_user.username
    assert user.first_name == created_user.first_name
    assert user.last_name == created_user.last_name
    assert user.language_code == created_user.language_code
    assert user.is_bot == created_user.is_bot
    assert user.is_premium == created_user.is_premium
    assert user.created_at == created_user.created_at
    assert user.updated_at == created_user.updated_at


@pytest.mark.asyncio
async def test_get_nonexistent_user(user_repo):
    """Test getting a nonexistent user."""
    user = await user_repo.get_user(999999999)
    assert user is None


@pytest.mark.asyncio
async def test_get_or_create_user_new(user_repo):
    """Test get_or_create_user with a new user."""
    user = await user_repo.get_or_create_user(
        user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
    )

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
async def test_get_or_create_user_existing(user_repo):
    """Test get_or_create_user with an existing user."""
    # Create user first
    created_user = await user_repo.create_user(
        user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
    )

    # Try to get or create the same user
    user = await user_repo.get_or_create_user(
        user_id=123456789,
        username="new_username",  # Different username
        first_name="New",  # Different first name
        last_name="Name",  # Different last name
        language_code="ru",  # Different language
        is_bot=True,  # Different is_bot
    )

    # Should return existing user without changes
    assert user.id == created_user.id
    assert user.username == created_user.username
    assert user.first_name == created_user.first_name
    assert user.last_name == created_user.last_name
    assert user.language_code == created_user.language_code
    assert user.is_bot == created_user.is_bot
    assert user.is_premium == created_user.is_premium
    assert user.created_at == created_user.created_at
    assert user.updated_at == created_user.updated_at
