"""Handlers for profile management."""
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import database as db_module


class ProfileHandlers:
    """Profile-related handlers."""

    async def show_profile_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        user_id = update.effective_user.id

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            await db.get_or_create_user(telegram_id=user_id)

        keyboard = [
            [InlineKeyboardButton("⚙️ Настройка промпта", callback_data="set_prompt")],
            [InlineKeyboardButton("📋 Специфические инструкции", callback_data="set_instructions")],
            [InlineKeyboardButton("👁 Показать текущие настройки", callback_data="show_settings")],
            [InlineKeyboardButton("📊 Статистика", callback_data="show_stats")],
            [InlineKeyboardButton("ℹ️ Информация о пользователе", callback_data="user_info")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
        ]

        await query.edit_message_text(
            "👤 **Профиль**\n\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

        return self.PROFILE_MENU

    async def profile_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_main":
            return await self.back_to_main_menu(update, context)
        if query.data == "profile":
            return await self.show_profile_menu(update, context)
        if query.data == "set_prompt":
            await query.edit_message_text(
                "⚙️ **Настройка промпта**\n\n"
                "Отправьте новый системный промпт для AI.\n"
                "Это повлияет на стиль и поведение ответов.\n\n"
                "Для отмены напишите /cancel",
                parse_mode="Markdown",
            )
            return self.PROMPT_SETTING
        if query.data == "set_instructions":
            await query.edit_message_text(
                "📋 **Специфические инструкции**\n\n"
                "Отправьте дополнительные инструкции для AI.\n"
                "Например: 'Отвечай кратко', 'Используй примеры', и т.д.\n\n"
                "Для отмены напишите /cancel",
                parse_mode="Markdown",
            )
            return self.INSTRUCTIONS_SETTING
        if query.data == "show_settings":
            return await self.show_current_settings(update, context)
        if query.data == "show_stats":
            return await self.show_statistics(update, context)
        if query.data == "user_info":
            return await self.show_user_info(update, context)

        return self.PROFILE_MENU

    async def set_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        new_prompt = update.message.text

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            await db.update_user_profile(telegram_id=user_id, custom_prompt=new_prompt)

        await update.message.reply_text("✅ Промпт успешно обновлен!", reply_markup=self.get_back_keyboard())
        return self.MAIN_MENU

    async def set_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        new_instructions = update.message.text

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            await db.update_user_profile(
                telegram_id=user_id,
                specific_instructions=new_instructions,
            )

        await update.message.reply_text(
            "✅ Инструкции успешно обновлены!",
            reply_markup=self.get_back_keyboard(),
        )
        return self.MAIN_MENU

    async def show_current_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        user_id = update.effective_user.id

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            user = await db.get_or_create_user(telegram_id=user_id)

        settings_text = (
            "👁 **Текущие настройки**\n\n"
            f"**Промпт:** {user.custom_prompt or 'Стандартный'}\n\n"
            f"**Инструкции:** {user.specific_instructions or 'Не заданы'}\n\n"
            f"**Max токенов:** {user.max_tokens}\n"
            f"**Temperature:** {user.temperature}"
        )

        await query.edit_message_text(
            settings_text,
            reply_markup=self.get_back_to_profile_keyboard(),
            parse_mode="Markdown",
        )

        return self.PROFILE_MENU

    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        user_id = update.effective_user.id

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            stats = await db.get_user_statistics(user.id)

        stats_text = (
            "📊 **Статистика использования**\n\n"
            f"**Всего сообщений:** {stats.get('total_messages', 0)}\n"
            f"**Токенов использовано:** {stats.get('total_tokens_used', 0)}\n"
            f"**Конспектов создано:** {stats.get('notes_count', 0)}\n"
            f"**Диалогов:** {stats.get('conversations_count', 0)}\n"
            f"**Зарегистрирован:** {stats.get('member_since', 'Неизвестно')}\n"
            f"**Последняя активность:** {stats.get('last_active', 'Неизвестно')}"
        )

        await query.edit_message_text(
            stats_text,
            reply_markup=self.get_back_to_profile_keyboard(),
            parse_mode="Markdown",
        )

        return self.PROFILE_MENU

    async def show_user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        user = update.effective_user

        info_text = (
            "ℹ️ <b>Информация о пользователе</b>\n\n"
            f"<b>ID:</b> {escape(str(user.id))}\n"
            f"<b>Имя:</b> {escape(user.first_name or 'Не указано')}\n"
            f"<b>Фамилия:</b> {escape(user.last_name or 'Не указана')}\n"
            f"<b>Username:</b> @{escape(user.username) if user.username else 'Не указан'}\n"
            f"<b>Язык:</b> {escape(user.language_code or 'Не определен')}"
        )

        await query.edit_message_text(
            info_text,
            reply_markup=self.get_back_to_profile_keyboard(),
            parse_mode="HTML",
        )

        return self.PROFILE_MENU
