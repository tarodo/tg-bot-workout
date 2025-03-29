from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.db.repositories import UserRepository
from bot.main import echo, help_command, start
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_start():
    """Test /start command."""
    # Mock update and context
    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.effective_user.language_code = "en"
    update.effective_user.is_bot = False
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.bot_data = {}

    # Mock user repository
    mock_user_repo = AsyncMock(spec=UserRepository)
    mock_user_repo.get_or_create_user.return_value = MagicMock(
        id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )

    # Mock async session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.__aenter__.return_value = mock_session

    with patch("bot.main.async_session", return_value=mock_session), patch(
        "bot.main.UserRepository", return_value=mock_user_repo
    ):
        await start(update, context)

    # Verify that get_or_create_user was called with correct parameters
    mock_user_repo.get_or_create_user.assert_called_once_with(
        user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
    )

    # Verify that update.message.reply_text was called
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_help():
    """Test /help command."""
    # Mock update and context
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await help_command(update, context)

    # Verify that update.message.reply_text was called
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_echo():
    """Test echo command."""
    # Mock update and context
    update = MagicMock()
    update.message.text = "Test message"
    update.message.reply_text = AsyncMock()
    update.message.delete = AsyncMock()
    context = MagicMock()

    await echo(update, context)

    # Verify that update.message.reply_text was called with the same text
    update.message.reply_text.assert_called_once_with("Test message new")
    update.message.delete.assert_called_once()
