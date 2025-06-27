from bot.keyboards import get_main_keyboard
from telegram import Update
from telegram.ext import ContextTypes

from ..db.database import async_session
from ..db.repositories import UserRepository
from ..logging import get_logger
from ..user_state import UserDataManager

logger = get_logger(__name__)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show main menu, handling /start and main_menu callbacks."""
    user_state = UserDataManager(context)

    # Handle /start command: create user, send a new message
    if update.message and update.message.text == "/start":
        user = update.effective_user
        async with async_session() as session:
            user_repo = UserRepository(session)
            await user_repo.get_or_create_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
                is_bot=user.is_bot,
            )
        logger.info("Start command received", user_id=user.id, username=user.username)
        msg_text = (
            f"Привет, {update.effective_user.full_name}! "
            "Я бот для тренировок.\nВыбери тип тренировки"
        )
        main_keyboard = get_main_keyboard()

        welcome_message = await update.effective_chat.send_message(
            msg_text,
            reply_markup=main_keyboard,
        )
        user_state.update_message(
            chat_id=welcome_message.chat_id, message_id=welcome_message.message_id
        )

    # Handle main_menu callback: edit existing message
    elif update.callback_query:
        query = update.callback_query
        await query.answer()

        last_bot_message = user_state.get_active_message()
        msg_text = "Главное меню\nВыбери тип тренировки:"
        main_keyboard = get_main_keyboard()

        if last_bot_message:
            await context.bot.edit_message_text(
                chat_id=last_bot_message.chat_id,
                message_id=last_bot_message.message_id,
                text=msg_text,
                reply_markup=main_keyboard,
            )
        else:
            # Fallback: if no message to edit, send a new one
            welcome_message = await update.effective_chat.send_message(
                msg_text,
                reply_markup=main_keyboard,
            )
            user_state.update_message(
                chat_id=welcome_message.chat_id, message_id=welcome_message.message_id
            )

    # Reset conversation state
    if context.user_data.get("conversation"):
        context.user_data["conversation"] = None

    return 0  # MAIN_MENU state
