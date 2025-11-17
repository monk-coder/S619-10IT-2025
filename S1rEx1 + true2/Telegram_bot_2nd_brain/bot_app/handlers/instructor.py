"""Handlers for instructor mode."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from config import config
from openrouter_client import openrouter_client

from ..responses import instructor as instructor_responses
from ..services import db_session


class InstructorHandlers:
    """Instructor mode interactions."""

    async def start_instructor_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query

        await query.edit_message_text(
            instructor_responses.instructor_intro(),
            parse_mode="Markdown",
        )

        return self.INSTRUCTOR_TOPIC

    async def handle_instructor_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        topic = update.message.text
        context.user_data['instructor_topic'] = topic

        keyboard = [[KeyboardButton("Начальный")], [KeyboardButton("Средний")], [KeyboardButton("Продвинутый")]]

        await update.message.reply_text(
            instructor_responses.instructor_level_prompt(topic),
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

        async with db_session(self.db_manager_class) as (_, db):
            user = await db.get_or_create_user(telegram_id=user_id)
            custom_instructions = user.specific_instructions
            user_model = user.preferred_model or config.model_name

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        response = await openrouter_client.instructor_mode(
            topic=topic,
            question=text,
            level=level,
            custom_instructions=custom_instructions,
            model=user_model,
        )

        await update.message.reply_text(response, parse_mode="Markdown")

        keyboard = [
            [InlineKeyboardButton("❓ Задать еще вопрос", callback_data="more_instructor")],
            [InlineKeyboardButton("🔄 Сменить тему", callback_data="instructor")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
        ]

        await update.message.reply_text(
            instructor_responses.instructor_followup_prompt(),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return self.MAIN_MENU
