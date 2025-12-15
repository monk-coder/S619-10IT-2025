from telebot import types
from bot_instance import bot
from utils import log_action, send_main_menu
from models import ensure_user

# Импорты функций для кнопок
from handlers.profile_handlers import show_profile, start_profile_edit
from handlers.wishlist_handlers import send_wishlist_view, start_add_item_flow, prompt_wishlist_deletion
from handlers.game_handlers import start_create_game_flow, send_owner_status, start_join_game, start_leave_game, start_participants_lookup, start_mix_game, show_my_recipient

# Определяем BUTTON_ACTIONS
BUTTON_ACTIONS = {
    "👤 Профиль": show_profile,
    "✏️ Обновить профиль": start_profile_edit,
    "🎁 Мой вишлист": lambda message: send_wishlist_view(message.chat.id, message.from_user.id),
    "➕ Добавить подарок": start_add_item_flow,
    "❌ Удалить подарок": prompt_wishlist_deletion,
    "🎲 Создать игру": start_create_game_flow,
    "🔔 Мои игры": send_owner_status,
    "🎮 Вступить в игру": start_join_game,
    "🚪 Выйти из игры": start_leave_game,
    "👥 Участники игры": start_participants_lookup,
    "🎉 Провести жеребьёвку": start_mix_game,
    "🎁 Кому дарю?": show_my_recipient,
    "🏠 Главное меню": lambda message: send_main_menu(message.chat.id, "🏠 Главное меню. Выберите действие:"),
}

def setup_basic_handlers():
    @bot.message_handler(commands=["start"])
    def cmd_start(message: types.Message) -> None:
        user = message.from_user
        ensure_user(user.id, user.username)
        log_action("command_start", user_id=user.id, username=user.username)
        send_main_menu(message.chat.id, 
            "🎅 Добро пожаловать в Тайного Санту!\nИспользуйте кнопки ниже или /help, чтобы узнать подробности.")

    @bot.message_handler(commands=["help"])
    def cmd_help(message: types.Message) -> None:
        log_action("command_help", user_id=message.from_user.id)
        bot.send_message(
            message.chat.id,
            """<b>Команды и кнопки</b>
🎅 /menu — открыть главное меню
👤 /profile — показать профиль
✏️ /edit_profile — обновить профиль
🎁 /wishlist — вишлист с кнопками удаления
➕ /add_item — добавить подарок
🎲 /create_game — создать игру
🔔 /status — мои игры как организатора
🎮 /join CODE — вступить в игру по коду
🚪 /leave CODE — выйти из игры до жеребьёвки
👥 /participants CODE — участники игры
🎉 /mix CODE — провести жеребьёвку (то же, что /send)
🎁 /my_recipient — показать вашего получателя
❓ /ask сообщение — задать анонимный вопрос

Или просто выбирайте действия в главном меню!""",
        )

    def is_main_button(message: types.Message) -> bool:
        return message.content_type == "text" and message.text in BUTTON_ACTIONS

    @bot.message_handler(func=is_main_button)
    def handle_main_buttons(message: types.Message) -> None:
        action = BUTTON_ACTIONS.get(message.text)
        if action:
            log_action("button_press", user_id=message.from_user.id, button=message.text)
            action(message)