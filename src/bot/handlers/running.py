import logging
from datetime import datetime
from itertools import islice

from bot.keyboards import get_main_keyboard
from bot.user_state import UserDataManager
from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

from ..db.database import async_session
from ..db.models.training import TrainingProgram, UserTrainingProgram, UserWorkout, Workout
from .common import show_main_menu

logger = logging.getLogger(__name__)

# States
SHOW_PROGRAMS, SHOW_PROGRAM_MENU, SHOW_WORKOUTS, SHOW_WORKOUT_DETAILS, SHOW_END_WORKOUT = range(5)

# Callback data patterns
CALLBACK_PATTERNS = {
    "running": "^running$",
    "program": "^program_",
    "show_program": "^show_program_",
    "workout": "^workout_",
    "back_to_programs": "^back_to_programs$",
    "main_menu": "^main_menu$",
    "reg_program": "^reg_program_",
    "end_program": "^end_program_",
    "give_active_workout": "^give_active_workout$",
    "end_workout": "^end_workout_",
}


def create_programs_keyboard(
    programs: list[TrainingProgram], active_programs_ids: list[int]
) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for programs list."""
    id_to_name = {
        p.id: p.name if p.id not in active_programs_ids else f"✅ {p.name} (продолжить)"
        for p in programs
    }
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"program_{id}")]
        for id, name in id_to_name.items()
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    return keyboard


def create_program_menu_keyboard(
    program_id: int, active_program: bool
) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for program menu."""
    if active_program:
        return [
            [
                InlineKeyboardButton("Продолжить тренировки", callback_data="give_active_workout"),
                InlineKeyboardButton(
                    "Список тренировок", callback_data=f"show_program_{program_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "Завершить программу", callback_data=f"end_program_{program_id}"
                )
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_programs")],
        ]

    return [
        [
            InlineKeyboardButton("Я в деле", callback_data=f"reg_program_{program_id}"),
            InlineKeyboardButton("Список тренировок", callback_data=f"show_program_{program_id}"),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_programs")],
    ]


def create_workouts_keyboard(
    workouts: list[Workout], program_id: int
) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for workouts list."""
    buttons = [
        InlineKeyboardButton(str(w.order), callback_data=f"workout_{w.id}") for w in workouts
    ]
    keyboard = []
    it = iter(buttons)
    keyboard.extend([list(islice(it, 5)) for _ in range(0, len(buttons), 5)])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"program_{program_id}")])
    return keyboard


def create_workout_details_keyboard(
    program_id: int, workout_id: int, is_active_workout: bool = False
) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for workout details."""
    if is_active_workout:
        return [
            [
                InlineKeyboardButton(
                    "⬅️ Завершить тренировку", callback_data=f"end_workout_{program_id}_{workout_id}"
                )
            ],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")],
        ]
    else:
        return [
            [
                InlineKeyboardButton(
                    "⬅️ К списку тренировок", callback_data=f"show_program_{program_id}"
                )
            ],
            [InlineKeyboardButton("⬅️ К описанию программы", callback_data=f"program_{program_id}")],
        ]


def create_end_workout_keyboard(program_id: int) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for end workout."""
    return [
        [InlineKeyboardButton("Следующая тренировка", callback_data="give_active_workout")],
        [InlineKeyboardButton("Список тренировок", callback_data=f"show_program_{program_id}")],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")],
    ]


async def running_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show running programs menu."""
    query = update.callback_query
    if query:
        await query.answer()

    try:
        async with async_session() as session:
            # Get all training programs
            programs = await session.execute(TrainingProgram.__table__.select())
            programs = programs.fetchall()

            active_programs = await get_unfinished_programs(update.effective_user.id)
            active_programs_ids = [p.id for p in active_programs]

        keyboard = create_programs_keyboard(programs, active_programs_ids)
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Выберите программу тренировок:"

        if query:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text=text, reply_markup=reply_markup)

        return SHOW_PROGRAMS
    except Exception as e:
        logger.error(f"Error in running_menu: {e}", exc_info=True)
        await query.edit_message_text(
            text="Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
        return int(ConversationHandler.END)


async def show_program_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show program menu."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    try:
        program_id = int(query.data.split("_")[1])
        async with async_session() as session:
            # Get program
            program = await session.get(TrainingProgram, program_id)

        if not program:
            await query.edit_message_text(
                text="Программа не найдена. Попробуйте еще раз.",
                reply_markup=get_main_keyboard(),
            )
            return int(ConversationHandler.END)

        # Check if user has active program
        registered = await get_unfinished_programs(user_id)
        active_program = False
        if len(registered) == 1:
            active_program = registered[0].id == program_id

        keyboard = create_program_menu_keyboard(program_id, active_program)
        text = f"Программа: {program.name}\n{program.description}\nВыберите действие:"

        try:
            await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise

        return SHOW_PROGRAM_MENU
    except Exception as e:
        logger.error(f"Error in show_program_menu: {e}", exc_info=True)
        await query.edit_message_text(
            text="Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
        return int(ConversationHandler.END)


async def show_program_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show workouts for selected program."""
    query = update.callback_query
    await query.answer()

    try:
        program_id = int(query.data.split("_")[-1])

        async with async_session() as session:
            # Get program and its workouts
            program = await session.get(TrainingProgram, program_id)
            if not program:
                await query.edit_message_text(
                    text="Программа не найдена. Попробуйте еще раз.",
                    reply_markup=get_main_keyboard(),
                )
                return int(ConversationHandler.END)

            workouts = await session.execute(
                Workout.__table__.select()
                .where(Workout.program_id == program_id)
                .order_by(Workout.order)
            )
            workouts = workouts.fetchall()

        keyboard = create_workouts_keyboard(workouts, program_id)
        text = f"Программа: {program.name}\n{program.description}\nВыберите тренировку:"

        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        return SHOW_WORKOUTS
    except Exception as e:
        logger.error(f"Error in show_program_workouts: {e}", exc_info=True)
        await query.edit_message_text(
            text="Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
        return int(ConversationHandler.END)


async def show_workout_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    workout_id: int,
    is_active_workout: bool = False,
) -> int:
    """Show details for selected workout."""
    user_state = UserDataManager(context)
    last_bot_message = user_state.get_active_message()

    try:
        async with async_session() as session:
            # Get workout and its program
            workout = await session.get(Workout, workout_id)
            if not workout:
                text = "Тренировка не найдена. Попробуйте еще раз."
                keyboard = get_main_keyboard()
                await context.bot.edit_message_text(
                    chat_id=last_bot_message.chat_id,
                    message_id=last_bot_message.message_id,
                    text=text,
                    reply_markup=keyboard,
                )
                return int(ConversationHandler.END)

            program = await session.get(TrainingProgram, workout.program_id)

        keyboard = create_workout_details_keyboard(program.id, workout.id, is_active_workout)
        text = (
            f"Программа: {program.name}\n"
            f"Тренировка: {workout.order}\n\n"
            f"🎯 Описание:\n{workout.description}\n\n"
            f"🏃‍♂️ План тренировки:\n{workout.plan}\n\n"
            f"🔥 СБУ:\n{workout.warmup}\n\n"
        )
        if last_bot_message:
            await context.bot.edit_message_text(
                chat_id=last_bot_message.chat_id,
                message_id=last_bot_message.message_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        return SHOW_WORKOUT_DETAILS

    except Exception as e:
        logger.error(f"Error in show_workout_details: {e}", exc_info=True)
        text = "Произошла ошибка. Попробуйте позже."
        keyboard = get_main_keyboard()
        await context.bot.edit_message_text(
            chat_id=last_bot_message.chat_id,
            message_id=last_bot_message.message_id,
            text=text,
            reply_markup=keyboard,
        )
        return int(ConversationHandler.END)


async def handle_workout_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show details for selected workout."""
    query = update.callback_query
    await query.answer()
    workout_id = int(query.data.split("_")[1])

    return await show_workout_details(update, context, workout_id)


async def get_unfinished_programs(user_id: int) -> list[TrainingProgram]:
    """Get unfinished programs for user."""
    async with async_session() as session:
        stmt = (
            select(TrainingProgram)
            .join(UserTrainingProgram)
            .where(
                UserTrainingProgram.user_id == user_id,
                UserTrainingProgram.end_date.is_(None),
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def register_program(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Register program."""
    query = update.callback_query
    await query.answer()

    try:
        program_id = int(query.data.split("_")[-1])
        async with async_session() as session:
            # Get program
            user_id = update.effective_user.id

            # Check for unfinished programs
            unfinished_programs = await get_unfinished_programs(user_id)

            if unfinished_programs:
                await query.edit_message_text(
                    text=(
                        "У вас уже есть незавершенная программа тренировок.\n"
                        "Завершите ее, прежде чем начать новую."
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("⬅️ Назад", callback_data="running")]]
                    ),
                )
                return SHOW_PROGRAMS

            # Register program
            user_program = UserTrainingProgram(user_id=user_id, program_id=program_id)
            session.add(user_program)
            await session.commit()

            await query.edit_message_text(
                text="Программа успешно зарегистрирована. Начинайте тренировки!",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Назад", callback_data="running")]]
                ),
            )
            return SHOW_PROGRAMS
    except Exception as e:
        logger.error(f"Error in register_program: {e}", exc_info=True)
        await query.edit_message_text(
            text="Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
        return int(ConversationHandler.END)


async def end_program(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End program."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    try:
        program_id = int(query.data.split("_")[-1])
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

        await query.edit_message_text(
            text="Программа успешно завершена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data="running")]]
            ),
        )
        return SHOW_PROGRAMS
    except Exception as e:
        logger.error(f"Error in end_program: {e}", exc_info=True)
        await query.edit_message_text(
            text="Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
        return int(ConversationHandler.END)


async def get_active_program(user_id: int) -> UserTrainingProgram | None:
    """Get active program for user."""
    try:
        async with async_session() as session:
            stmt = select(UserTrainingProgram).where(
                UserTrainingProgram.user_id == user_id,
                UserTrainingProgram.end_date.is_(None),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error in get_active_program: {e}", exc_info=True)
        return None


async def get_last_workout_id(user_id: int, user_program: UserTrainingProgram) -> int | None:
    """Get last workout for user."""
    try:
        async with async_session() as session:
            stmt = (
                select(UserWorkout)
                .where(
                    UserWorkout.user_id == user_id,
                    UserWorkout.user_program_id == user_program.program_id,
                )
                .order_by(UserWorkout.finished_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            last_workout = result.scalar_one_or_none()
            logger.info(f"Last workout: {last_workout.id}")
            return last_workout.workout_id if last_workout else None
    except Exception as e:
        logger.error(f"Error in get_last_workout: {e}", exc_info=True)
        return None


async def give_active_workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Give active workout."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    active_program = await get_active_program(user_id)
    if not active_program:
        await query.edit_message_text(
            text="У вас нет активной программы тренировок.",
            reply_markup=get_main_keyboard(),
        )
        return int(ConversationHandler.END)

    last_workout_id = await get_last_workout_id(user_id, active_program)
    logger.info(f"Last workout id: {last_workout_id}")
    active_workout_order = 1
    if last_workout_id:
        try:
            async with async_session() as session:
                workout = await session.get(Workout, last_workout_id)
                active_workout_order = workout.order + 1
        except Exception as e:
            logger.error(f"Error in get_active_workout: {e}", exc_info=True)
            return int(ConversationHandler.END)

    async with async_session() as session:
        try:
            stmt = select(Workout).where(
                Workout.program_id == active_program.program_id,
                Workout.order == active_workout_order,
            )
            result = await session.execute(stmt)
            workout = result.scalar_one_or_none()

            if not workout:
                await query.edit_message_text(
                    text="Тренировка не найдена. Возможно, вы уже завершили программу.",
                    reply_markup=get_main_keyboard(),
                )
                return int(ConversationHandler.END)
        except Exception as e:
            logger.error(f"Error in give_active_workout: {e}", exc_info=True)
            return int(ConversationHandler.END)

    return await show_workout_details(update, context, workout.id, True)


async def end_workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End workout."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    program_id, workout_id = map(int, query.data.split("_")[-2:])

    try:
        async with async_session() as session:
            # Get active program
            active_program = await get_active_program(user_id)
            if not active_program:
                await query.edit_message_text(
                    text="У вас нет активной программы тренировок.",
                    reply_markup=get_main_keyboard(),
                )
                return int(ConversationHandler.END)

            # Get workout
            workout = await session.get(Workout, workout_id)
            if not workout:
                await query.edit_message_text(
                    text="Тренировка не найдена.",
                    reply_markup=get_main_keyboard(),
                )
                return int(ConversationHandler.END)

            # Create user workout record
            user_workout = UserWorkout(
                user_id=user_id,
                workout_id=workout_id,
                user_program_id=active_program.id,
                finished_at=datetime.now(),
            )
            session.add(user_workout)
            await session.commit()

            text = f"🎉 Тренировка завершена!\n\n{workout.final_message}"
            keyboard = create_end_workout_keyboard(program_id)
            await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

            return SHOW_END_WORKOUT
    except Exception as e:
        logger.error(f"Error in end_workout: {e}", exc_info=True)
        return int(ConversationHandler.END)


def get_running_conversation_handler() -> ConversationHandler:
    """Get conversation handler for running training."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(running_menu, pattern=CALLBACK_PATTERNS["running"])],
        states={
            SHOW_PROGRAMS: [
                CallbackQueryHandler(show_program_menu, pattern=CALLBACK_PATTERNS["program"]),
            ],
            SHOW_PROGRAM_MENU: [
                CallbackQueryHandler(
                    show_program_workouts, pattern=CALLBACK_PATTERNS["show_program"]
                ),
                CallbackQueryHandler(running_menu, pattern=CALLBACK_PATTERNS["back_to_programs"]),
                CallbackQueryHandler(register_program, pattern=CALLBACK_PATTERNS["reg_program"]),
                CallbackQueryHandler(end_program, pattern=CALLBACK_PATTERNS["end_program"]),
                CallbackQueryHandler(
                    give_active_workout, pattern=CALLBACK_PATTERNS["give_active_workout"]
                ),
            ],
            SHOW_WORKOUTS: [
                CallbackQueryHandler(handle_workout_details, pattern=CALLBACK_PATTERNS["workout"]),
                CallbackQueryHandler(show_program_menu, pattern=CALLBACK_PATTERNS["program"]),
                CallbackQueryHandler(
                    show_program_workouts, pattern=CALLBACK_PATTERNS["show_program"]
                ),
            ],
            SHOW_WORKOUT_DETAILS: [
                CallbackQueryHandler(
                    show_program_workouts, pattern=CALLBACK_PATTERNS["show_program"]
                ),
                CallbackQueryHandler(show_program_menu, pattern=CALLBACK_PATTERNS["program"]),
                CallbackQueryHandler(end_workout, pattern=CALLBACK_PATTERNS["end_workout"]),
            ],
            SHOW_END_WORKOUT: [
                CallbackQueryHandler(
                    give_active_workout, pattern=CALLBACK_PATTERNS["give_active_workout"]
                ),
                CallbackQueryHandler(show_program_menu, pattern=CALLBACK_PATTERNS["program"]),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(show_main_menu, pattern=CALLBACK_PATTERNS["main_menu"]),
        ],
        name="running_conversation",
        allow_reentry=True,
    )
