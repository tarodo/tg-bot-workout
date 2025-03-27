from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Update
from telegram import User as TelegramUser
from telegram.ext import ContextTypes

from src.bot.main import echo, help_command, start


@pytest.mark.asyncio
async def test_start():
    """Test /start command."""
    # Create mock update
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=TelegramUser)
    update.effective_user.id = 123456789
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.effective_user.language_code = "en"
    update.effective_user.is_bot = False
    # Mock full_name property
    update.effective_user.full_name = "Test User"
    update.message.reply_text = AsyncMock()

    # Create mock context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # Run command
    await start(update, context)

    # Check reply
    update.message.reply_text.assert_called_once_with(
        "Hello, Test User! I'm an echo bot. Send me a message."
    )


@pytest.mark.asyncio
async def test_help():
    """Test /help command."""
    # Create mock update
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=TelegramUser)
    update.effective_user.id = 123456789
    update.message.reply_text = AsyncMock()

    # Create mock context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # Run command
    await help_command(update, context)

    # Check reply
    update.message.reply_text.assert_called_once_with(
        "I just repeat your messages. Send me some text!"
    )


@pytest.mark.asyncio
async def test_echo():
    """Test echo handler."""
    # Create mock update
    update = MagicMock(spec=Update)
    update.message.text = "Hello, World!"
    update.message.reply_text = AsyncMock()

    # Create mock context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # Run handler
    await echo(update, context)

    # Check reply
    update.message.reply_text.assert_called_once_with("Hello, World! new")
