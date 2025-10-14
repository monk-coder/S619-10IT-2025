"""Handlers for instructor mode."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

import database as db_module
from openrouter_client import openrouter_client


class InstructorHandlers:
    """Instructor mode interactions."""

    async def start_instructor_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query

        await query.edit_message_text(
            "👨‍🏫 **Режим Инструктора**\n\n"
            "Введите тему, которую хотите изучить:",
            parse_mode="Markdown",
        )

        return self.INSTRUCTOR_TOPIC

    async def handle_instructor_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        topic = update.message.text
        context.user_data['instructor_topic'] = topic

        keyboard = [[KeyboardButton("Начальный")], [KeyboardButton("Средний")], [KeyboardButton("Продвинутый")]]

        await update.message.reply_text(
            f"📚 Тема: **{topic}**\n\n"
            "Выберите уровень сложности:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
            parse_mode="Markdown",
        )

        return self.INSTRUCTOR_QUESTION

    async def handle_instructor_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        text = update.message.text

        if text in ["Начальный", "Средний", "Продвинутый"]:
            level_map = {
                "Начальный": "beginner",
                "Средний": "intermediate",
                "Продвинутый": "advanced",
            }
            context.user_data['instructor_level'] = level_map[text]

            await update.message.reply_text(
                "Отлично! Теперь задайте ваш вопрос по теме:",
                reply_markup=ReplyKeyboardRemove(),
            )
            return self.INSTRUCTOR_QUESTION

        topic = context.user_data.get('instructor_topic', 'General')
        level = context.user_data.get('instructor_level', 'intermediate')

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            custom_instructions = user.specific_instructions

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        response = await openrouter_client.instructor_mode(
            topic=topic,
            question=text,
            level=level,
            custom_instructions=custom_instructions,
        )

        await update.message.reply_text(response, parse_mode="Markdown")

        keyboard = [
            [InlineKeyboardButton("❓ Задать еще вопрос", callback_data="more_instructor")],
            [InlineKeyboardButton("🔄 Сменить тему", callback_data="instructor")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
        ]

        await update.message.reply_text(
            "Что дальше?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return self.MAIN_MENU
