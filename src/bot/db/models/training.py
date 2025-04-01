from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
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
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
    )

    user_training_programs: Mapped[list["UserTrainingProgram"]] = relationship(
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
    user_workouts: Mapped[list["UserWorkout"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
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

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_training_programs")
    program: Mapped["TrainingProgram"] = relationship(back_populates="user_training_programs")
    user_workouts: Mapped[list["UserWorkout"]] = relationship(
        back_populates="user_training_program",
        cascade="all, delete-orphan",
    )


class UserWorkout(Base):
    """User workout association model."""

    __tablename__ = "user_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    workout_id: Mapped[int] = mapped_column(Integer, ForeignKey("workouts.id"))
    user_program_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_training_programs.id"))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "workout_id", "user_program_id", name="uix_user_workout_program"
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_workouts")
    workout: Mapped["Workout"] = relationship(back_populates="user_workouts")
    user_training_program: Mapped["UserTrainingProgram"] = relationship(
        back_populates="user_workouts"
    )
