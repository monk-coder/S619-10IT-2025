from telebot import types
from typing import Any, Dict
from bot_instance import bot
from utils import log_action, set_step, pop_step, get_step
from models import update_profile, add_wish_item, create_game, add_participant
from handlers.game_handlers import join_game_by_code, leave_game_by_code, show_participants_by_code, mix_game_by_code


def handle_profile_fullname(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка шага ввода ФИО"""
    payload["full_name"] = message.text.strip()
    set_step(message.from_user.id, "profile_bio", payload)
    log_action("step_profile_fullname", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Расскажите о себе (хобби, интересы):")
    return True


def handle_profile_bio(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка шага ввода описания профиля"""
    full_name = payload.get("full_name", "")
    update_profile(message.from_user.id, full_name, message.text.strip())
    pop_step(message.from_user.id)
    log_action("step_profile_completed", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Профиль обновлён.")
    return True


def handle_wish_description(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка шага ввода описания подарка"""
    payload["description"] = message.text.strip()
    set_step(message.from_user.id, "wish_photo", payload)
    log_action("step_wish_description", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Пришлите фото для пожелания или напишите 'пропустить'.")
    return True


def handle_wish_photo_skip(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка пропуска фото подарка"""
    add_wish_item(message.from_user.id, payload.get("description", ""), None)
    pop_step(message.from_user.id)
    log_action("step_wish_photo_skipped", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Подарок добавлен без фото.")
    return True


def handle_wish_photo_upload(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка загрузки фото подарка"""
    file_id = message.photo[-1].file_id
    add_wish_item(message.from_user.id, payload.get("description", ""), file_id)
    pop_step(message.from_user.id)
    log_action("step_wish_photo_uploaded", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Подарок добавлен с фото.")
    return True


def handle_wish_photo(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка шага добавления фото подарка"""
    if message.content_type == "text" and message.text.lower() == "пропустить":
        return handle_wish_photo_skip(message, payload)
    
    if message.content_type == "photo":
        return handle_wish_photo_upload(message, payload)
    
    bot.send_message(message.chat.id, "Пришлите фото или напишите 'пропустить'.")
    return True


def handle_game_title(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка шага ввода названия игры"""
    payload["title"] = message.text.strip()
    set_step(message.from_user.id, "game_draw_date", payload)
    log_action("step_game_title", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Укажите дату жеребьёвки (например, 24 декабря):")
    return True


def handle_game_draw_date(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка шага ввода даты жеребьёвки"""
    payload["draw_date"] = message.text.strip()
    set_step(message.from_user.id, "game_minimum", payload)
    log_action("step_game_draw_date", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Минимальное количество участников (>=3):")
    return True


def handle_game_minimum(message: types.Message, payload: Dict[str, Any]) -> bool:
    """Обработка шага ввода минимального количества участников"""
    try:
        minimum = max(3, int(message.text.strip()))
    except ValueError:
        bot.send_message(message.chat.id, "Введите число не меньше трёх.")
        return True
    
    payload["minimum"] = minimum
    game = create_game(message.from_user.id, payload.get("title", ""), payload.get("draw_date", ""), minimum)
    add_participant(game.id, message.from_user.id)
    pop_step(message.from_user.id)
    log_action("step_game_created", user_id=message.from_user.id, code=game.code)
    bot.send_message(
        message.chat.id,
        f"Игра создана! Код приглашения: <code>{game.code}</code>. Отправьте его участникам.",
    )
    return True


def handle_cancel_step(message: types.Message, action: str) -> bool:
    """Обработка отмены любого шага"""
    pop_step(message.from_user.id)
    log_action(f"step_{action}_cancel", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "Действие отменено.")
    return True


def handle_code_action(message: types.Message, action: str, code: str) -> bool:
    """Обработка действий с кодами игр"""
    handlers = {
        "join_code": lambda: join_game_by_code(message.from_user.id, message.chat.id, code),
        "leave_code": lambda: leave_game_by_code(message.from_user.id, message.chat.id, code),
        "participants_code": lambda: show_participants_by_code(message, code),
        "mix_code": lambda: mix_game_by_code(message, code)
    }
    
    if action in handlers and handlers[action]():
        pop_step(message.from_user.id)
        return True
    
    return False


def handle_code_steps(message: types.Message, step: Dict[str, Any]) -> bool:
    """Обработка шагов с кодами игр"""
    action = step["action"]
    code = message.text.strip()
    
    # Обработка отмены
    if code.lower() in {"отмена", "cancel"}:
        return handle_cancel_step(message, action)
    
    if not code:
        bot.send_message(message.chat.id, "Введите код игры:")
        return True
    
    return handle_code_action(message, action, code)


def handle_profile_steps(message: types.Message, step: Dict[str, Any]) -> bool:
    """Обработка шагов редактирования профиля"""
    action = step["action"]
    payload = step.get("payload", {})
    
    profile_handlers = {
        "profile_fullname": lambda: handle_profile_fullname(message, payload),
        "profile_bio": lambda: handle_profile_bio(message, payload)
    }
    
    if action in profile_handlers:
        return profile_handlers[action]()
    
    return False


def handle_wishlist_steps(message: types.Message, step: Dict[str, Any]) -> bool:
    """Обработка шагов добавления подарка"""
    action = step["action"]
    payload = step.get("payload", {})
    
    wishlist_handlers = {
        "wish_description": lambda: handle_wish_description(message, payload),
        "wish_photo": lambda: handle_wish_photo(message, payload)
    }
    
    if action in wishlist_handlers:
        return wishlist_handlers[action]()
    
    return False


def handle_game_steps(message: types.Message, step: Dict[str, Any]) -> bool:
    """Обработка шагов создания игры"""
    action = step["action"]
    payload = step.get("payload", {})
    
    game_handlers = {
        "game_title": lambda: handle_game_title(message, payload),
        "game_draw_date": lambda: handle_game_draw_date(message, payload),
        "game_minimum": lambda: handle_game_minimum(message, payload)
    }
    
    if action in game_handlers:
        return game_handlers[action]()
    
    return False


def handle_text_step(message: types.Message, step: Dict[str, Any]) -> bool:
    """Основной обработчик пошаговых действий"""
    action = step["action"]
    
    # Профиль
    if action.startswith("profile_"):
        return handle_profile_steps(message, step)
    
    # Вишлист
    if action.startswith("wish_"):
        return handle_wishlist_steps(message, step)
    
    # Создание игры
    if action.startswith("game_"):
        return handle_game_steps(message, step)
    
    # Действия с кодами
    if action.endswith("_code"):
        return handle_code_steps(message, step)
    
    return False


def handle_unknown_command(message: types.Message) -> None:
    """Обработка неизвестных команд"""
    log_action("unknown_text", user_id=message.from_user.id, text=message.text)
    bot.send_message(message.chat.id, "Не понял команду. Нажмите кнопку в меню или /help.")


def setup_step_handlers():
    """Настройка обработчиков пошаговых действий"""

    @bot.message_handler(content_types=["text", "photo"])
    def handle_message(message: types.Message) -> None:
        """Обработка всех сообщений"""
        step = get_step(message.from_user.id)

        if step and handle_text_step(message, step):
            return
        
        if message.content_type == "text" and not message.text.startswith("/"):
            handle_unknown_command(message)
