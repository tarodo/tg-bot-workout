from bot.handlers.main_menu import get_main_menu_conversation_handler
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from .config import get_settings
from .logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize settings
settings = get_settings()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is received."""
    logger.info("Help command received", user_id=update.effective_user.id)
    await update.message.reply_text("I just repeat your messages. Send me some text!")


def main() -> None:
    """Start the bot."""

    # Create the Application and pass it your bot's token
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(get_main_menu_conversation_handler())

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
