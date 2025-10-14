"""Handlers for main menu interactions."""
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import database as db_module


class MainMenuHandlers:
    """Main menu related handlers."""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.effective_user
        self.logger.info("User %s started the bot", user.id)

        async with db_module.AsyncSessionLocal() as session:
            db = self.db_manager_class(session)
            await db.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )

        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "Я - образовательный бот с AI от DeepSeek V3.\n"
            "Выберите режим работы:"
        )

        await update.message.reply_text(welcome_text, reply_markup=self.build_main_menu_keyboard())
        return self.MAIN_MENU

    async def main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_main":
            return await self.back_to_main_menu(update, context)
        if query.data == "profile":
            return await self.show_profile_menu(update, context)
        if query.data == "notes":
            return await self.start_notes_mode(update, context)
        if query.data == "extract":
            return await self.start_extract_mode(update, context)
        if query.data == "instructor":
            return await self.start_instructor_mode(update, context)
        if query.data == "search":
            return await self.start_search_mode(update, context)

        return self.MAIN_MENU
