"""Handlers for profile management."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from ..responses import profile as profile_responses
from ..services import db_session


class ProfileHandlers:
    """Profile-related handlers."""

    async def show_profile_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        user_id = update.effective_user.id

        async with db_session(self.db_manager_class) as (_, db):
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
            profile_responses.profile_menu_intro(),
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
                profile_responses.prompt_setting_message(),
                parse_mode="Markdown",
            )
            return self.PROMPT_SETTING
        if query.data == "set_instructions":
            await query.edit_message_text(
                profile_responses.instructions_setting_message(),
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

        async with db_session(self.db_manager_class) as (_, db):
            await db.update_user_profile(telegram_id=user_id, custom_prompt=new_prompt)

        await update.message.reply_text("✅ Промпт успешно обновлен!", reply_markup=self.get_back_keyboard())
        return self.MAIN_MENU

    async def set_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        new_instructions = update.message.text

        async with db_session(self.db_manager_class) as (_, db):
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

        async with db_session(self.db_manager_class) as (_, db):
            user = await db.get_or_create_user(telegram_id=user_id)

        settings_text = profile_responses.current_settings_text(
            custom_prompt=user.custom_prompt,
            instructions=user.specific_instructions,
            max_tokens=user.max_tokens,
            temperature=user.temperature,
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

        async with db_session(self.db_manager_class) as (_, db):
            user = await db.get_or_create_user(telegram_id=user_id)
            stats = await db.get_user_statistics(user.id)

        stats_text = profile_responses.statistics_text(stats)

        await query.edit_message_text(
            stats_text,
            reply_markup=self.get_back_to_profile_keyboard(),
            parse_mode="Markdown",
        )

        return self.PROFILE_MENU

    async def show_user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        user_id = update.effective_user.id

        async with db_session(self.db_manager_class) as (_, db):
            user = await db.get_or_create_user(telegram_id=user_id)

        info_text = profile_responses.user_info_text(user_context=user.specific_instructions)

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📝 Поделиться информацией", callback_data="set_instructions")],
                [InlineKeyboardButton("🔙 Назад", callback_data="profile")],
            ]
        )

        await query.edit_message_text(
            info_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

        return self.PROFILE_MENU
