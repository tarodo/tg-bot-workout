from itertools import islice

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
SHOW_PROGRAMS, SHOW_PROGRAM_MENU, SHOW_WORKOUTS, SHOW_WORKOUT_DETAILS = range(4)


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


async def show_program_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show program menu."""
    query = update.callback_query
    await query.answer()

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

        keyboard = []
        keyboard.append(
            [
                InlineKeyboardButton("Я в деле", callback_data="main_menu"),
                InlineKeyboardButton("План программы", callback_data=f"show_program_{program.id}"),
            ]
        )
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_programs")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"Программа: {program.name}\n{program.description}\nВыберите действие:"

        await query.edit_message_text(text=text, reply_markup=reply_markup)

    return SHOW_PROGRAM_MENU


async def show_program_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show workouts for selected program."""
    query = update.callback_query
    await query.answer()

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

        keyboard = []
        buttons = [
            InlineKeyboardButton(str(w.order), callback_data=f"workout_{w.id}") for w in workouts
        ]
        it = iter(buttons)
        keyboard.extend([list(islice(it, 5)) for _ in range(0, len(buttons), 5)])

        # Add back button
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"program_{program.id}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"Программа: {program.name}\n{program.description}\nВыберите тренировку:"

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
            [
                InlineKeyboardButton(
                    "⬅️ К списку тренировок", callback_data=f"show_program_{program.id}"
                )
            ],
            [InlineKeyboardButton("⬅️ К описанию программы", callback_data=f"program_{program.id}")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"Программа: {program.name}\n"
            f"Тренировка: {workout.order}\n\n"
            f"🎯 Описание:\n{workout.description}\n\n"
            f"🏃‍♂️ План тренировки:\n{workout.plan}\n\n"
            f"🔥 СБУ:\n{workout.warmup}\n\n"
        )

        await query.edit_message_text(text=text, reply_markup=reply_markup)

    return SHOW_WORKOUT_DETAILS


def get_running_conversation_handler() -> ConversationHandler:
    """Get conversation handler for running training."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(running_menu, pattern="^running$")],
        states={
            SHOW_PROGRAMS: [
                CallbackQueryHandler(show_program_menu, pattern="^program_"),
            ],
            SHOW_PROGRAM_MENU: [
                CallbackQueryHandler(show_program_workouts, pattern="^show_program_"),
                CallbackQueryHandler(running_menu, pattern="^back_to_programs$"),
            ],
            SHOW_WORKOUTS: [
                CallbackQueryHandler(show_workout_details, pattern="^workout_"),
                CallbackQueryHandler(show_program_menu, pattern="^program_"),
                CallbackQueryHandler(show_program_workouts, pattern="^show_program_"),
            ],
            SHOW_WORKOUT_DETAILS: [
                CallbackQueryHandler(show_program_workouts, pattern="^show_program_"),
                CallbackQueryHandler(show_program_menu, pattern="^program_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(show_main_menu, pattern="^main_menu$"),
        ],
        name="running_conversation",
        allow_reentry=True,
    )
