#!/usr/bin/env python

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import get_settings
from .db.base import get_db
from .db.repositories import UserRepository
from .echo import concat_new
from .logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is received."""
    user = update.effective_user

    # Get database session
    async for session in get_db():
        # Get or create user
        user_repo = UserRepository(session)
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

    await update.message.reply_text(f"Hello, {user.full_name}! I'm an echo bot. Send me a message.")


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

    # Use our function to append " new" to the message
    modified_message = concat_new(user_message)
    await update.message.reply_text(modified_message)


def main() -> None:
    """Starts the bot."""
    settings = get_settings()

    # Get token from environment variables
    token = settings.TELEGRAM_TOKEN
    logger.info("Starting bot")

    # Create application
    application = Application.builder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start the bot
    logger.info("Bot is running")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
