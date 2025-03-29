from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import get_settings
from .db.base import async_session
from .db.repositories import UserRepository
from .echo import concat_new
from .logging import get_logger, setup_logging
from .user_state import UserDataManager

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize settings
settings = get_settings()


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
        welcome_message = await update.message.reply_text(
            f"Hello, {user.full_name}! I'm an echo bot. Send me a message."
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


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echoes back any incoming message."""
    user_message = update.message.text
    logger.info(
        "Message received",
        user_id=update.effective_user.id,
        message=user_message,
    )

    # Get user state and last bot message
    user_state = UserDataManager(context)
    last_bot_message = user_state.get_active_message()

    # Delete user's message
    await update.message.delete()

    # Use our function to append " new" to the message
    modified_message = concat_new(user_message)

    if last_bot_message:
        # Edit existing bot message
        await context.bot.edit_message_text(
            chat_id=last_bot_message.chat_id,
            message_id=last_bot_message.message_id,
            text=modified_message,
        )
    else:
        # Send new message if no previous message exists
        new_message = await update.message.reply_text(modified_message)
        user_state.update_message(chat_id=new_message.chat_id, message_id=new_message.message_id)


def main() -> None:
    """Start the bot."""

    # Create the Application and pass it your bot's token
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
