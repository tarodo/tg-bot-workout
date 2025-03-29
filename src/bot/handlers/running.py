from bot.keyboards import get_main_keyboard
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

from ..db.database import async_session
from ..db.models.training import TrainingProgram, Workout
from .common import show_main_menu

# States
SHOW_PROGRAMS, SHOW_WORKOUTS = range(2)


async def running_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show running programs menu."""
    query = update.callback_query
    if query:
        await query.answer()

    async with async_session() as session:
        # Get all training programs
        programs = await session.execute(TrainingProgram.__table__.select())
        programs = programs.fetchall()

        keyboard = []
        for program in programs:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        program.name,
                        callback_data=f"program_{program.id}",
                    )
                ]
            )

        # Add back button
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Выберите программу тренировок:"

        if query:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text=text, reply_markup=reply_markup)

    return SHOW_PROGRAMS


async def show_program_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show workouts for selected program."""
    query = update.callback_query
    await query.answer()

    program_id = int(query.data.split("_")[1])

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

        keyboard = []
        for workout in workouts:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"Тренировка {workout.order}",
                        callback_data=f"workout_{workout.id}",
                    )
                ]
            )

        # Add back button
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"Программа: {program.name}\n\n{program.description}\n\nВыберите тренировку:"

        await query.edit_message_text(text=text, reply_markup=reply_markup)

    return SHOW_WORKOUTS


async def show_workout_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show details for selected workout."""
    query = update.callback_query
    await query.answer()

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

        keyboard = [
            [InlineKeyboardButton("⬅️ К списку тренировок", callback_data=f"program_{program.id}")],
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="main_menu")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"Программа: {program.name}\n"
            f"Тренировка {workout.order}\n\n"
            f"🎯 Описание:\n{workout.description}\n\n"
            f"🔥 Разминка:\n{workout.warmup}\n\n"
            f"🏃‍♂️ План тренировки:\n{workout.plan}\n\n"
        )

        await query.edit_message_text(text=text, reply_markup=reply_markup)

    return SHOW_WORKOUTS


def get_running_conversation_handler() -> ConversationHandler:
    """Get conversation handler for running training."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(running_menu, pattern="^running$")],
        states={
            SHOW_PROGRAMS: [
                CallbackQueryHandler(show_program_workouts, pattern="^program_"),
                CallbackQueryHandler(running_menu, pattern="^back_to_programs$"),
            ],
            SHOW_WORKOUTS: [
                CallbackQueryHandler(show_workout_details, pattern="^workout_"),
                CallbackQueryHandler(show_program_workouts, pattern="^program_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(show_main_menu, pattern="^main_menu$"),
        ],
        name="running_conversation",
        allow_reentry=True,
    )
