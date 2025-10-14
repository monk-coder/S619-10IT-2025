"""Handlers for notes management."""
from telegram import Update
from telegram.ext import ContextTypes

import database as db_module
from openrouter_client import openrouter_client


class NotesHandlers:
    """Notes-related interactions."""

    async def start_notes_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query

        await query.edit_message_text(
            "📝 **Режим конспектов**\n\n"
            "Введите тему конспекта:",
            parse_mode="Markdown",
        )

        return self.NOTES_TOPIC

    async def handle_notes_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        topic = update.message.text
        context.user_data['notes_topic'] = topic

        await update.message.reply_text(
            f"📝 Тема: **{topic}**\n\n"
            "Теперь отправьте содержание конспекта:",
            parse_mode="Markdown",
        )

        return self.NOTES_CONTENT

    async def handle_notes_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        content = update.message.text
        topic = context.user_data.get('notes_topic', 'Без темы')
        user_id = update.effective_user.id

        summary = await openrouter_client.generate_summary(content)

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            await db.create_note(
                user_id=user.id,
                topic=topic,
                content=content,
                summary=summary,
            )

        await update.message.reply_text(
            f"✅ Конспект сохранен!\n\n"
            f"**Тема:** {topic}\n"
            f"**Краткое содержание:** {summary[:200]}...",
            reply_markup=self.get_back_keyboard(),
            parse_mode="Markdown",
        )

        return self.MAIN_MENU
