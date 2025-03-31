from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class TrainingProgram(Base):
    """Training program model."""

    __tablename__ = "training_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship(
        secondary="user_training_programs",
        back_populates="training_programs",
    )
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of the training program."""
        return f"<TrainingProgram {self.name}>"


class Workout(Base):
    """Workout model."""

    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("training_programs.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[str] = mapped_column(Text, nullable=False)
    warmup: Mapped[str] = mapped_column(Text, nullable=False)
    final_message: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(nullable=False)

    # Relationships
    program: Mapped["TrainingProgram"] = relationship(
        back_populates="workouts",
    )
    users: Mapped[list["User"]] = relationship(
        secondary="user_workouts",
        back_populates="workouts",
    )

    def __repr__(self) -> str:
        """String representation of the workout."""
        return f"<Workout {self.id}>"


class UserTrainingProgram(Base):
    """User training program association model."""

    __tablename__ = "user_training_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("training_programs.id"))
    start_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "program_id", "start_date", name="uix_user_program_start"),
    )


user_workouts = Table(
    "user_workouts",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.id"), primary_key=True),
    Column("workout_id", Integer, ForeignKey("workouts.id"), primary_key=True),
    Column("finished_at", DateTime(timezone=True), nullable=True),
)
