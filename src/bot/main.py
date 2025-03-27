import logging
import sys

import structlog
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import get_settings
from .echo import concat_new

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

# Structured logging configuration
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is received."""
    user = update.effective_user
    logger.info("Start command received", user_id=user.id, username=user.username)
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
