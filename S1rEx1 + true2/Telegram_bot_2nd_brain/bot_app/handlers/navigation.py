"""Navigation helpers and shared keyboard builders."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from ..responses import main_menu as main_menu_responses


class NavigationMixin:
    """Provide shared navigation helpers for the bot."""

    def build_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📝 Создание конспекта", callback_data="notes")],
            [InlineKeyboardButton("👨‍🏫 Инструктор", callback_data="instructor")],
            [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_back_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
        return InlineKeyboardMarkup(keyboard)

    def get_back_to_profile_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="profile")]]
        return InlineKeyboardMarkup(keyboard)

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query

        await query.edit_message_text(
            main_menu_responses.main_menu_prompt(),
            reply_markup=self.build_main_menu_keyboard(),
            parse_mode="Markdown",
        )

        return self.MAIN_MENU
