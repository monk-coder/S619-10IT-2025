"""Обработчики профиля."""
from telebot import types

from bot.bot import bot, send_profile_menu
from database import operations
from utils.helpers import log_action, format_profile, set_step

def show_profile(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    log_action("show_profile", user_id=message.from_user.id, username=message.from_user.username)
    bot.send_message(message.chat.id, format_profile(message.from_user.id))
    send_profile_menu(message.chat.id)

def start_profile_edit(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "profile_fullname", {})
    log_action("start_profile_edit", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "✏️ Введите ваше ФИО:")

@bot.message_handler(commands=["profile"])
def cmd_profile(message: types.Message) -> None:
    show_profile(message)

@bot.message_handler(commands=["edit_profile"])
def cmd_edit_profile(message: types.Message) -> None:
    start_profile_edit(message)