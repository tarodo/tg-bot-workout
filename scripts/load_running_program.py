import asyncio
import os
from pathlib import Path

import yaml  # type: ignore
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.db.database import async_session
from src.bot.db.models.training import TrainingProgram, Workout


async def load_program(session: AsyncSession, program_data: dict) -> None:
    """Load program data into database."""
    # Create program
    program_name = program_data["program_name"]
    program_description = program_data["program_description"]

    result = await session.execute(
        select(TrainingProgram).where(TrainingProgram.name == program_name)
    )
    print(f"Program {program_name} already exists")
    program = result.scalar_one_or_none()
    if not program:
        program = TrainingProgram(
            name=program_name,
            description=program_description,
        )
        session.add(program)
        await session.flush()  # Get program.id

    # Create workouts
    for workout_data in program_data["workouts"]:
        workout = await session.execute(
            select(Workout).where(
                (Workout.order == workout_data["number"]) & (Workout.program_id == program.id)
            )
        )
        if workout.scalar_one_or_none():
            print(f"Workout {workout_data['number']} already exists")
            continue
        workout = Workout(
            program_id=program.id,
            description=workout_data["description"],
            plan=workout_data["plan"],
            warmup=workout_data["sbu"],
            final_message=workout_data["final_msg"],
            order=workout_data["number"],
        )
        session.add(workout)

    await session.commit()


async def main() -> None:
    """Load program data from YAML to database."""
    # Determine YAML file path based on environment
    training_list = ["run_health", "run_start"]
    for training in training_list:
        if os.getenv("DOCKER_CONTAINER"):
            # Running in Docker
            yaml_path = Path(f"/app/trainings/{training}.yaml")
        else:
            # Running locally
            yaml_path = Path(__file__).parent.parent / "trainings" / f"{training}.yaml"

        if not yaml_path.exists():
            print(f"Error: File {yaml_path} not found!")
            continue
        with open(yaml_path, encoding="utf-8") as f:
            program_data = yaml.safe_load(f)

        # Load data into database
        async with async_session() as session:
            await load_program(session, program_data)
            print("Program loaded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
