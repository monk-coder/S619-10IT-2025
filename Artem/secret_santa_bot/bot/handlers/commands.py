"""Обработчики кнопок и текстовых команд."""
from telebot import types

from bot.bot import bot, send_main_menu
from database import operations
from utils.helpers import log_action, get_step, handle_text_step

# Действия для кнопок - теперь это словарь строк, а не функций
BUTTON_ACTIONS = {
    "👤 Мой профиль": "show_profile",
    "✏️ Редактировать профиль": "start_profile_edit", 
    "🎁 Мой вишлист": "show_wishlist",
    "➕ Добавить желание": "start_add_item",
    "🗑️ Удалить желание": "prompt_remove_item",
    "🎄 Создать игру": "start_create_game",
    "📋 Мои игры": "show_owner_games",
    "🎮 Присоединиться": "start_join_game",
    "🚪 Покинуть игру": "start_leave_game",
    "👥 Участники": "start_participants_lookup",
    "🎉 Провести жеребьёвку": "start_mix_game",
    "🎯 Кому я дарю?": "show_my_recipient",
    "🏠 Главное меню": "show_main_menu",
    "❓ Задать вопрос": "start_ask_santa",
}

def is_main_button(message: types.Message) -> bool:
    return message.content_type == "text" and message.text in BUTTON_ACTIONS

@bot.message_handler(func=is_main_button)
def handle_main_buttons(message: types.Message) -> None:
    action_name = BUTTON_ACTIONS.get(message.text)
    if not action_name:
        return
    
    log_action("button_press", user_id=message.from_user.id, button=message.text)
    
    # Импортируем обработчики внутри функции чтобы избежать циклических импортов
    if action_name == "show_profile":
        from bot.handlers.profile import show_profile
        show_profile(message)
    elif action_name == "start_profile_edit":
        from bot.handlers.profile import start_profile_edit
        start_profile_edit(message)
    elif action_name == "show_wishlist":
        from bot.handlers.wishlist import send_wishlist_view
        send_wishlist_view(message.chat.id, message.from_user.id)
    elif action_name == "start_add_item":
        from bot.handlers.wishlist import start_add_item_flow
        start_add_item_flow(message)
    elif action_name == "prompt_remove_item":
        from bot.handlers.wishlist import prompt_wishlist_deletion
        prompt_wishlist_deletion(message)
    elif action_name == "start_create_game":
        from bot.handlers.games import start_create_game_flow
        start_create_game_flow(message)
    elif action_name == "show_owner_games":
        from bot.handlers.games import send_owner_status
        send_owner_status(message)
    elif action_name == "start_join_game":
        from bot.handlers.games import start_join_game
        start_join_game(message)
    elif action_name == "start_leave_game":
        from bot.handlers.games import start_leave_game
        start_leave_game(message)
    elif action_name == "start_participants_lookup":
        from bot.handlers.games import start_participants_lookup
        start_participants_lookup(message)
    elif action_name == "start_mix_game":
        from bot.handlers.games import start_mix_game
        start_mix_game(message)
    elif action_name == "show_my_recipient":
        from bot.handlers.games import show_my_recipient
        show_my_recipient(message)
    elif action_name == "show_main_menu":
        send_main_menu(message.chat.id, "🏠 Главное меню")
    elif action_name == "start_ask_santa":
        from bot.handlers.games import start_ask_santa
        start_ask_santa(message)

@bot.message_handler(content_types=["text", "photo"])
def handle_message(message: types.Message) -> None:
    step = get_step(message.from_user.id)
    if step:
        if handle_text_step(message, step):
            return
    
    if message.content_type == "text" and not message.text.startswith("/"):
        log_action("unknown_text", user_id=message.from_user.id, text=message.text)
        bot.send_message(
            message.chat.id, 
            "❌ Не понял команду. Используйте кнопки меню или /help для справки."
        )