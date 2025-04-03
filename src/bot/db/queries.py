from datetime import datetime

from sqlalchemy import select

from ..db.database import async_session
from ..db.models.training import TrainingProgram, UserTrainingProgram, UserWorkout, Workout


async def get_active_program(user_id: int) -> UserTrainingProgram | None:
    """Get active program for user."""
    async with async_session() as session:
        stmt = select(UserTrainingProgram).where(
            UserTrainingProgram.user_id == user_id,
            UserTrainingProgram.end_date.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore


async def get_last_workout(user_id: int, user_program_id: int) -> Workout | None:
    """Get last workout for user."""
    async with async_session() as session:
        stmt = (
            select(Workout)
            .join(UserWorkout.workout)
            .where(
                UserWorkout.user_id == user_id,
                UserWorkout.user_program_id == user_program_id,
            )
            .order_by(UserWorkout.finished_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore


async def get_active_workout(user_id: int) -> tuple[Workout | None, bool]:
    """Get next workout for active program."""
    is_last_workout = False
    user_program = await get_active_program(user_id)
    if not user_program:
        return None, is_last_workout

    last_workout = await get_last_workout(user_id, user_program.id)
    last_workout_order = 0
    if last_workout:
        last_workout_order = last_workout.order

    async with async_session() as session:
        stmt = (
            select(Workout)
            .where(
                Workout.program_id == user_program.program_id,
                Workout.order > last_workout_order,
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        workout = result.scalar_one_or_none()
        if not workout:
            is_last_workout = True
        return workout, is_last_workout


async def get_program_workouts(program_id: int) -> list[Workout]:
    """Get all workouts for a program."""
    async with async_session() as session:
        stmt = select(Workout).where(Workout.program_id == program_id).order_by(Workout.order)
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_workout_by_id(workout_id: int) -> Workout | None:
    """Get workout by ID."""
    async with async_session() as session:
        return await session.get(Workout, workout_id)  # type: ignore


async def get_program_by_id(program_id: int) -> TrainingProgram | None:
    """Get program by ID."""
    async with async_session() as session:
        return await session.get(TrainingProgram, program_id)  # type: ignore


async def register_user_program(user_id: int, program_id: int) -> None:
    """Register user for a program."""
    async with async_session() as session:
        user_program = UserTrainingProgram(user_id=user_id, program_id=program_id)
        session.add(user_program)
        await session.commit()


async def end_user_program(user_id: int, program_id: int) -> None:
    """End user's program."""
    async with async_session() as session:
        stmt = select(UserTrainingProgram).where(
            UserTrainingProgram.user_id == user_id,
            UserTrainingProgram.program_id == program_id,
            UserTrainingProgram.end_date.is_(None),
        )
        result = await session.execute(stmt)
        user_program = result.scalar_one()
        user_program.end_date = datetime.now()
        await session.commit()


async def record_workout_completion(user_id: int, workout_id: int, user_program_id: int) -> None:
    """Record that user completed a workout."""
    async with async_session() as session:
        user_workout = UserWorkout(
            user_id=user_id,
            workout_id=workout_id,
            user_program_id=user_program_id,
            finished_at=datetime.now(),
        )
        session.add(user_workout)
        await session.commit()


async def get_all_programs() -> list[TrainingProgram]:
    """Get all training programs."""
    async with async_session() as session:
        result = await session.execute(TrainingProgram.__table__.select())
        return list(result.fetchall())


async def get_workout_by_program_and_order(program_id: int, order: int) -> Workout | None:
    """Get workout by program ID and order number."""
    async with async_session() as session:
        stmt = select(Workout).where(
            Workout.program_id == program_id,
            Workout.order == order,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore
