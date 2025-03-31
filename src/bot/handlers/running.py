import logging
from itertools import islice

from bot.keyboards import get_main_keyboard
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

from ..db.database import async_session
from ..db.models.training import TrainingProgram, Workout
from .common import show_main_menu

logger = logging.getLogger(__name__)

# States
SHOW_PROGRAMS, SHOW_PROGRAM_MENU, SHOW_WORKOUTS, SHOW_WORKOUT_DETAILS = range(4)

# Callback data patterns
CALLBACK_PATTERNS = {
    "running": "^running$",
    "program": "^program_",
    "show_program": "^show_program_",
    "workout": "^workout_",
    "back_to_programs": "^back_to_programs$",
    "main_menu": "^main_menu$",
}


def create_programs_keyboard(programs: list[TrainingProgram]) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for programs list."""
    keyboard = [
        [InlineKeyboardButton(program.name, callback_data=f"program_{program.id}")]
        for program in programs
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    return keyboard


def create_program_menu_keyboard(program_id: int) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for program menu."""
    return [
        [
            InlineKeyboardButton("Я в деле", callback_data="main_menu"),
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


def create_workout_details_keyboard(program_id: int) -> list[list[InlineKeyboardButton]]:
    """Create keyboard for workout details."""
    return [
        [InlineKeyboardButton("⬅️ К списку тренировок", callback_data=f"show_program_{program_id}")],
        [InlineKeyboardButton("⬅️ К описанию программы", callback_data=f"program_{program_id}")],
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

        keyboard = create_programs_keyboard(programs)
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

        keyboard = create_program_menu_keyboard(program_id)
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


async def show_workout_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show details for selected workout."""
    query = update.callback_query
    await query.answer()

    try:
        workout_id = int(query.data.split("_")[1])

        async with async_session() as session:
            # Get workout and its program
            workout = await session.get(Workout, workout_id)
            if not workout:
                await query.edit_message_text(
                    text="Тренировка не найдена. Попробуйте еще раз.",
                    reply_markup=get_main_keyboard(),
                )
                return int(ConversationHandler.END)

            program = await session.get(TrainingProgram, workout.program_id)

        keyboard = create_workout_details_keyboard(program.id)
        text = (
            f"Программа: {program.name}\n"
            f"Тренировка: {workout.order}\n\n"
            f"🎯 Описание:\n{workout.description}\n\n"
            f"🏃‍♂️ План тренировки:\n{workout.plan}\n\n"
            f"🔥 СБУ:\n{workout.warmup}\n\n"
        )

        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        return SHOW_WORKOUT_DETAILS
    except Exception as e:
        logger.error(f"Error in show_workout_details: {e}", exc_info=True)
        await query.edit_message_text(
            text="Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
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
            ],
            SHOW_WORKOUTS: [
                CallbackQueryHandler(show_workout_details, pattern=CALLBACK_PATTERNS["workout"]),
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
            ],
        },
        fallbacks=[
            CallbackQueryHandler(show_main_menu, pattern=CALLBACK_PATTERNS["main_menu"]),
        ],
        name="running_conversation",
        allow_reentry=True,
    )
