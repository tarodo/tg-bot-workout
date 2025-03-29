from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .training import TrainingProgram, Workout


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
    training_programs: Mapped[list["TrainingProgram"]] = relationship(
        secondary="user_training_programs",
        back_populates="users",
    )
    workouts: Mapped[list["Workout"]] = relationship(
        secondary="user_workouts",
        back_populates="users",
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.id} {self.username}>"
