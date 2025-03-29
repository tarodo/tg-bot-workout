from bot.keyboards import get_main_keyboard
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from .config import get_settings
from .db.database import async_session
from .db.repositories import UserRepository
from .logging import get_logger, setup_logging
from .user_state import UserDataManager

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize settings
settings = get_settings()


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu."""
    user_state = UserDataManager(context)
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
        welcome_message = await update.effective_chat.send_message(
            msg_text,
            reply_markup=main_keyboard,
        )
        user_state.update_message(
            chat_id=welcome_message.chat_id, message_id=welcome_message.message_id
        )


async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu callback query."""
    query = update.callback_query
    await query.answer()

    # Show main menu
    await show_main_menu(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is received."""
    user = update.effective_user

    async with async_session() as session:
        user_repo = UserRepository(session)
        # Get or create user
        db_user = await user_repo.get_or_create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_bot=user.is_bot,
        )

        logger.info(
            "Start command received",
            user_id=user.id,
            username=user.username,
            is_new_user=db_user.created_at == db_user.updated_at,
        )

        # Send welcome message and save its message_id
        main_keyboard = get_main_keyboard()
        welcome_message = await update.message.reply_text(
            f"Привет, {user.full_name}! Я бот для тренировок.\nВыбери тип тренировки",
            reply_markup=main_keyboard,
        )

        # Save message info for future editing
        user_state = UserDataManager(context)
        user_state.update_message(
            chat_id=welcome_message.chat_id, message_id=welcome_message.message_id
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is received."""
    logger.info("Help command received", user_id=update.effective_user.id)
    await update.message.reply_text("I just repeat your messages. Send me some text!")


def main() -> None:
    """Start the bot."""

    # Create the Application and pass it your bot's token
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_main_menu_callback, pattern="^main_menu$"))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
