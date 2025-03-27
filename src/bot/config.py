import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Telegram Bot Token
    TELEGRAM_TOKEN: str | None = Field(None, description="Telegram Bot API Token")

    # Database settings
    DATA_DIR: str = Field(default="data", description="Directory for database files")
    DB_NAME: str = Field(default="bot.db", description="Database filename")

    @property
    def database_url(self) -> str:
        """Get database URL."""
        return f"sqlite+aiosqlite:///{os.path.join(self.DATA_DIR, self.DB_NAME)}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
