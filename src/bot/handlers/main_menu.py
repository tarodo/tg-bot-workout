from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)

from .common import show_main_menu
from .running import get_running_conversation_handler

# States
MAIN_MENU = 0


def get_main_menu_conversation_handler() -> ConversationHandler:
    """Get conversation handler for main menu."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", show_main_menu),
            CallbackQueryHandler(show_main_menu, pattern="^main_menu$"),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(show_main_menu, pattern="^main_menu$"),
                get_running_conversation_handler(),
            ],
        },
        fallbacks=[],
        name="main_menu_conversation",
    )
