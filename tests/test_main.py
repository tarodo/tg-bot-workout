from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.db.repositories import UserRepository
from bot.main import handle_main_menu_callback, help_command, show_main_menu, start
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
async def test_show_main_menu_new():
    """Test showing main menu when no previous message exists."""
    # Mock update and context
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.send_message = AsyncMock()
    update.effective_chat.send_message.return_value = MagicMock(chat_id=123, message_id=456)

    context = MagicMock()
    context.user_data = {"state_obj": {"bot_message": None, "state": "initial", "data": {}}}

    await show_main_menu(update, context)

    # Verify that send_message was called with correct text and keyboard
    update.effective_chat.send_message.assert_called_once()
    call_args = update.effective_chat.send_message.call_args.args
    assert "Главное меню" in call_args[0]
    assert "reply_markup" in update.effective_chat.send_message.call_args.kwargs


@pytest.mark.asyncio
async def test_show_main_menu_edit():
    """Test showing main menu by editing existing message."""
    # Mock update and context
    update = MagicMock()
    context = MagicMock()
    context.bot.edit_message_text = AsyncMock()
    context.user_data = {
        "state_obj": {
            "bot_message": {"chat_id": 123, "message_id": 456},
            "state": "initial",
            "data": {},
        }
    }

    await show_main_menu(update, context)

    # Verify that edit_message_text was called with correct parameters
    context.bot.edit_message_text.assert_called_once()
    call_args = context.bot.edit_message_text.call_args.kwargs
    assert call_args["chat_id"] == 123
    assert call_args["message_id"] == 456
    assert "Главное меню" in call_args["text"]
    assert "reply_markup" in call_args


@pytest.mark.asyncio
async def test_handle_main_menu_callback():
    """Test main menu callback handler."""
    # Mock update and context
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.effective_chat = MagicMock()
    update.effective_chat.send_message = AsyncMock()
    update.effective_chat.send_message.return_value = MagicMock(chat_id=123, message_id=456)

    context = MagicMock()
    context.user_data = {"state_obj": {"bot_message": None, "state": "initial", "data": {}}}

    await handle_main_menu_callback(update, context)

    # Verify callback query was answered
    update.callback_query.answer.assert_called_once()

    # Verify new message was sent
    update.effective_chat.send_message.assert_called_once()
    call_args = update.effective_chat.send_message.call_args.args
    assert "Главное меню" in call_args[0]
    assert "reply_markup" in update.effective_chat.send_message.call_args.kwargs
