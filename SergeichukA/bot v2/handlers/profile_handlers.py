from telebot import types
from bot_instance import bot
from utils import log_action, send_main_menu, format_profile, set_step
from models import ensure_user, update_profile

def setup_profile_handlers():
    @bot.message_handler(commands=["menu"])
    def cmd_menu(message: types.Message) -> None:
        log_action("command_menu", user_id=message.from_user.id)
        send_main_menu(message.chat.id, "🏠 Главное меню. Выберите действие:")

    @bot.message_handler(commands=["profile"])
    def cmd_profile(message: types.Message) -> None:
        show_profile(message)

    @bot.message_handler(commands=["edit_profile"])
    def cmd_edit_profile(message: types.Message) -> None:
        start_profile_edit(message)

def show_profile(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    log_action("show_profile", user_id=message.from_user.id, username=message.from_user.username)
    bot.send_message(message.chat.id, format_profile(message.from_user.id))

def start_profile_edit(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "profile_fullname", {})
    log_action("start_profile_edit", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "✏️ Введите ваше ФИО:")