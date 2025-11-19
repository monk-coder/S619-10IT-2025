"""Базовые обработчики."""
import logging

from telebot import types

from bot.bot import bot, send_main_menu
from database import operations
from utils.helpers import log_action

logger = logging.getLogger("secret_santa_bot")

@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message) -> None:
    user = message.from_user
    operations.ensure_user(user.id, user.username)
    log_action("command_start", user_id=user.id, username=user.username)
    send_main_menu(
        message.chat.id,
        "🎅 <b>Добро пожаловать в Тайного Санту!</b>\n\n"
        "Здесь вы можете организовать обмен подарками с друзьями, "
        "составить вишлист и стать Тайным Сантой для кого-то особенного!",
    )

@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message) -> None:
    log_action("command_help", user_id=message.from_user.id)
    bot.send_message(
        message.chat.id,
        """<b>🎅 Помощь по боту Тайный Санта</b>

<b>Основные команды:</b>
/start - Запустить бота
/menu - Главное меню
/profile - Мой профиль
/wishlist - Мой вишлист
/create - Создать игру
/games - Мои игры
/recipient - Мой получатель

<b>Быстрые команды:</b>
/join CODE - Присоединиться к игре
/leave CODE - Покинуть игру
/participants CODE - Участники игры
/mix CODE - Провести жеребьёвку
/ask ВОПРОС - Задать вопрос Санте

<b>Или используйте кнопки меню для удобства!</b>""",
    )

@bot.message_handler(commands=["menu"])
def cmd_menu(message: types.Message) -> None:
    log_action("command_menu", user_id=message.from_user.id)
    send_main_menu(message.chat.id, "🏠 Главное меню")