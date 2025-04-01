from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .training import UserTrainingProgram, UserWorkout


class User(Base):
    """Telegram user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_bot: Mapped[bool] = mapped_column(default=False)
    is_premium: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user_training_programs: Mapped[list["UserTrainingProgram"]] = relationship(
        back_populates="user"
    )
    user_workouts: Mapped[list["UserWorkout"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.id} {self.username}>"
