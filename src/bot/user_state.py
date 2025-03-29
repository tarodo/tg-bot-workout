from dataclasses import asdict, dataclass, field
from typing import Any, Self

from telegram.ext import CallbackContext


@dataclass(frozen=True)
class BotMessage:
    """Represents a bot message that will be updated."""

    chat_id: int
    message_id: int


@dataclass
class UserState:
    """Data structure for storing user state."""

    bot_message: BotMessage | None = None
    state: str = "initial"
    data: dict[str, Any] = field(default_factory=dict)


class UserDataManager:
    """Manages user data with an abstraction over the telegram context."""

    def __init__(self, context: CallbackContext) -> None:
        """
        Initialize the user data manager.

        Args:
            context: Telegram bot context
        """
        self.context = context

        # Initialize state from user_data or create a new one
        if not context.user_data.get("state_obj"):
            context.user_data["state_obj"] = asdict(UserState())

    def get_state(self) -> UserState:
        """
        Get the current user state.

        Returns:
            UserState: Object with user state
        """
        state_dict = self.context.user_data["state_obj"]

        # Process the nested BotMessage object
        bot_message_dict = state_dict.get("bot_message")
        bot_message = None
        if bot_message_dict and isinstance(bot_message_dict, dict):
            try:
                bot_message = BotMessage(
                    chat_id=bot_message_dict.get("chat_id", 0),
                    message_id=bot_message_dict.get("message_id", 0),
                )
            except (TypeError, ValueError):
                bot_message = None

        return UserState(
            bot_message=bot_message, state=state_dict["state"], data=state_dict["data"]
        )

    def save_state(self, state: UserState) -> None:
        """
        Save the user state.

        Args:
            state: Updated user state
        """
        state_dict = asdict(state)
        self.context.user_data["state_obj"] = state_dict

    def update_state(self, *, state: str | None = None, **data_updates: Any) -> Self:
        """
        Update the user state.

        Args:
            state: New state (if needs to be changed)
            **data_updates: Additional data to update in state.data

        Returns:
            Self: Returns self for method chaining
        """
        current_state = self.get_state()

        if state is not None:
            current_state.state = state

        if data_updates:
            current_state.data.update(data_updates)

        self.save_state(current_state)
        return self

    def update_message(self, chat_id: int, message_id: int) -> Self:
        """
        Update information about the active bot message.

        Args:
            chat_id: Chat ID
            message_id: Message ID

        Returns:
            Self: Returns self for method chaining
        """
        state = self.get_state()
        state.bot_message = BotMessage(chat_id=chat_id, message_id=message_id)
        self.save_state(state)
        return self

    def get_active_message(self) -> BotMessage | None:
        """
        Get information about the active bot message.

        Returns:
            Optional[BotMessage]: Message information or None if no message exists yet
        """
        return self.get_state().bot_message

    def clear_data(self, keys: list[str] | None = None) -> Self:
        """
        Clear user data.

        Args:
            keys: List of keys to remove. If None, clears all data.

        Returns:
            Self: Returns self for method chaining
        """
        state = self.get_state()

        if keys is None:
            state.data.clear()
        else:
            for key in keys:
                state.data.pop(key, None)

        self.save_state(state)
        return self
