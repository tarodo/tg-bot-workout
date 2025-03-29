from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🏃 Беговая", callback_data="running"),
            InlineKeyboardButton("💪 Силовая", callback_data="strength"),
        ],
        [
            InlineKeyboardButton("👑 Главное меню", callback_data="main_menu"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)
