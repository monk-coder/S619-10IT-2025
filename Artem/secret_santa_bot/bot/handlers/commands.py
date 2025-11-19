"""Обработчики кнопок и текстовых команд."""
from telebot import types

from bot.bot import bot, send_main_menu
from database import operations
from utils.helpers import log_action, get_step, handle_text_step

# Словарь маршрутизации действий
ACTION_HANDLERS = {
    # Профиль
    "show_profile": {
        "module": "bot.handlers.profile",
        "function": "show_profile",
        "args": ["message"]
    },
    "start_profile_edit": {
        "module": "bot.handlers.profile", 
        "function": "start_profile_edit",
        "args": ["message"]
    },
    
    # Вишлист
    "show_wishlist": {
        "module": "bot.handlers.wishlist",
        "function": "send_wishlist_view", 
        "args": ["message.chat.id", "message.from_user.id"]
    },
    "start_add_item": {
        "module": "bot.handlers.wishlist",
        "function": "start_add_item_flow",
        "args": ["message"]
    },
    "prompt_remove_item": {
        "module": "bot.handlers.wishlist",
        "function": "prompt_wishlist_deletion",
        "args": ["message"]
    },
    
    # Игры
    "start_create_game": {
        "module": "bot.handlers.games",
        "function": "start_create_game_flow",
        "args": ["message"]
    },
    "show_owner_games": {
        "module": "bot.handlers.games",
        "function": "send_owner_status", 
        "args": ["message"]
    },
    "start_join_game": {
        "module": "bot.handlers.games",
        "function": "start_join_game",
        "args": ["message"]
    },
    "start_leave_game": {
        "module": "bot.handlers.games", 
        "function": "start_leave_game",
        "args": ["message"]
    },
    "start_participants_lookup": {
        "module": "bot.handlers.games",
        "function": "start_participants_lookup",
        "args": ["message"]
    },
    "start_mix_game": {
        "module": "bot.handlers.games",
        "function": "start_mix_game",
        "args": ["message"]
    },
    "show_my_recipient": {
        "module": "bot.handlers.games",
        "function": "show_my_recipient",
        "args": ["message"]
    },
    "start_ask_santa": {
        "module": "bot.handlers.games",
        "function": "start_ask_santa",
        "args": ["message"]
    },
    
    # Главное меню (встроенная функция)
    "show_main_menu": {
        "module": "builtin",
        "function": "send_main_menu",
        "args": ["message.chat.id", "'🏠 Главное меню'"]
    }
}

# Действия для кнопок
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

def _execute_action(action_name: str, message: types.Message) -> None:
    """Выполняет действие на основе его имени."""
    if action_name not in ACTION_HANDLERS:
        log_action("unknown_action", user_id=message.from_user.id, action=action_name)
        return
    
    handler_config = ACTION_HANDLERS[action_name]
    
    try:
        if handler_config["module"] == "builtin":
            # Встроенные функции
            if handler_config["function"] == "send_main_menu":
                send_main_menu(message.chat.id, "🏠 Главное меню")
        else:
            # Импортируем и выполняем функцию из модуля
            module = __import__(handler_config["module"], fromlist=[handler_config["function"]])
            function = getattr(module, handler_config["function"])
            
            # Подготавливаем аргументы
            args = []
            for arg in handler_config["args"]:
                if arg == "message":
                    args.append(message)
                elif arg == "message.chat.id":
                    args.append(message.chat.id)
                elif arg == "message.from_user.id":
                    args.append(message.from_user.id)
                else:
                    # Для строковых литералов
                    args.append(eval(arg))
            
            # Вызываем функцию
            function(*args)
            
        log_action("action_executed", user_id=message.from_user.id, action=action_name)
        
    except ImportError as e:
        log_action("import_error", user_id=message.from_user.id, action=action_name, error=str(e))
        bot.send_message(message.chat.id, "❌ Ошибка: модуль не найден")
    except AttributeError as e:
        log_action("function_error", user_id=message.from_user.id, action=action_name, error=str(e))
        bot.send_message(message.chat.id, "❌ Ошибка: функция не найдена")
    except Exception as e:
        log_action("action_error", user_id=message.from_user.id, action=action_name, error=str(e))
        bot.send_message(message.chat.id, "❌ Произошла ошибка при выполнении действия")

def is_main_button(message: types.Message) -> bool:
    return message.content_type == "text" and message.text in BUTTON_ACTIONS

@bot.message_handler(func=is_main_button)
def handle_main_buttons(message: types.Message) -> None:
    action_name = BUTTON_ACTIONS.get(message.text)
    if not action_name:
        log_action("button_not_found", user_id=message.from_user.id, button=message.text)
        return
    
    log_action("button_press", user_id=message.from_user.id, button=message.text)
    _execute_action(action_name, message)

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