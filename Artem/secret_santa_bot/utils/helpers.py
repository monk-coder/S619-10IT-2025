"""Вспомогательные функции."""
import logging
import random
from typing import Any, Dict, List, Optional, Tuple

import sqlite3
from telebot import types

from database import operations
from bot.bot import bot, send_profile_menu, send_wishlist_menu, send_game_menu, send_main_menu

logger = logging.getLogger("secret_santa_bot")

# Глобальный словарь для отслеживания состояний
pending_steps: Dict[int, Dict[str, Any]] = {}

def log_action(action: str, **payload: Any) -> None:
    if not payload:
        logger.info(action)
        return
    details = " ".join(f"{key}={value}" for key, value in payload.items())
    logger.info("%s %s", action, details)

def format_profile(user_id: int) -> str:
    profile = operations.get_profile(user_id)
    if not profile:
        return "❌ Профиль не найден."
    
    wishlist = operations.list_wishlist(user_id)
    lines = [
        "👤 <b>Ваш профиль:</b>",
        f"📝 <b>ФИО:</b> {profile['full_name'] or 'не указано'}",
        f"ℹ️ <b>О себе:</b> {profile['bio'] or 'не указано'}",
        "",
        "🎁 <b>Ваш вишлист:</b>"
    ]
    
    if not wishlist:
        lines.append("— пока пусто")
    else:
        for i, item in enumerate(wishlist, 1):
            lines.append(f"{i}. {item['description']}")
    
    return "\n".join(lines)

def build_wishlist_view(user_id: int) -> tuple[str, Optional[types.InlineKeyboardMarkup]]:
    items = operations.list_wishlist(user_id)
    lines = ["🎁 <b>Ваш вишлист:</b>"]
    
    if not items:
        lines.append("— пока пусто")
        return "\n".join(lines), None
    
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item['description']}")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for item in items:
        buttons.append(
            types.InlineKeyboardButton(
                text=f"🗑️ {item['id']}", callback_data=f"delete_wish:{item['id']}"
            )
        )
    
    # Распределяем кнопки по 2 в строке
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])
    
    return "\n".join(lines), markup

def send_wishlist_view(chat_id: int, user_id: int) -> None:
    text, markup = build_wishlist_view(user_id)
    log_action("view_wishlist", user_id=user_id)
    bot.send_message(chat_id, text, reply_markup=markup)
    from bot.bot import send_wishlist_menu
    send_wishlist_menu(chat_id)

def set_step(user_id: int, action: str, payload: Optional[Dict[str, Any]] = None) -> None:
    pending_steps[user_id] = {"action": action, "payload": payload or {}}

def pop_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.pop(user_id, None)

def get_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.get(user_id)

def ensure_owner(message: types.Message, game: operations.Game) -> bool:
    if message.from_user.id != game.owner_id:
        log_action("ensure_owner_denied", user_id=message.from_user.id, code=game.code)
        bot.send_message(message.chat.id, "❌ Только организатор может выполнить эту команду.")
        return False
    log_action("ensure_owner_ok", user_id=message.from_user.id, code=game.code)
    return True

def notify_pairs(game: operations.Game, pairs: Dict[int, int]) -> None:
    for santa_id, recipient_id in pairs.items():
        profile = operations.get_profile(recipient_id)
        wishlist = operations.list_wishlist(recipient_id)
        
        lines = [
            "🎅 <b>Поздравляем! Вы — Тайный Санта!</b>",
            f"🎄 <b>Игра:</b> {game.title}",
            "",
            "👤 <b>Ваш получатель:</b>",
            f"📝 <b>ФИО:</b> {profile['full_name'] or 'не указано'}",
            f"ℹ️ <b>О себе:</b> {profile['bio'] or 'не указано'}"
        ]
        
        if wishlist:
            lines.extend(["", "🎁 <b>Вишлист получателя:</b>"])
            for i, item in enumerate(wishlist, 1):
                lines.append(f"{i}. {item['description']}")
        else:
            lines.extend(["", "📭 <b>Вишлист пуст</b>"])
        
        log_action("notify_pair", game_id=game.id, santa_id=santa_id, recipient_id=recipient_id)
        bot.send_message(santa_id, "\n".join(lines))
        
        # Отправляем фото отдельно
        for item in wishlist:
            if item["photo_file_id"]:
                bot.send_photo(santa_id, item["photo_file_id"], caption=item["description"])

def add_wish_item(user_id: int, description: str, photo_file_id: Optional[str]) -> None:
    """Добавить пункт в вишлист"""
    operations.add_wish_item(user_id, description, photo_file_id)

def handle_text_step(message: types.Message, step: Dict[str, Any]) -> bool:
    """Обработка текстовых шагов (состояний)"""
    action = step["action"]
    payload = step.get("payload", {})
    
    if action == "profile_fullname":
        payload["full_name"] = message.text.strip()
        set_step(message.from_user.id, "profile_bio", payload)
        log_action("step_profile_fullname", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "📝 Расскажите о себе (хобби, интересы, увлечения):")
        return True
    
    if action == "profile_bio":
        full_name = payload.get("full_name", "")
        operations.update_profile(message.from_user.id, full_name, message.text.strip())
        pop_step(message.from_user.id)
        log_action("step_profile_completed", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "✅ Профиль успешно обновлён!")
        send_profile_menu(message.chat.id)
        return True
    
    if action == "wish_description":
        payload["description"] = message.text.strip()
        set_step(message.from_user.id, "wish_photo", payload)
        log_action("step_wish_description", user_id=message.from_user.id)
        bot.send_message(
            message.chat.id, 
            "🖼️ Пришлите фото подарка (опционально) или напишите \"пропустить\" чтобы продолжить без фото:"
        )
        return True
    
    if action == "wish_photo":
        if message.content_type == "text" and message.text.lower() == "пропустить":
            add_wish_item(message.from_user.id, payload.get("description", ""), None)
            pop_step(message.from_user.id)
            log_action("step_wish_photo_skipped", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "✅ Подарок добавлен в вишлист!")
            send_wishlist_menu(message.chat.id)
            return True
        
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            add_wish_item(message.from_user.id, payload.get("description", ""), file_id)
            pop_step(message.from_user.id)
            log_action("step_wish_photo_uploaded", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "✅ Подарок добавлен в вишлист с фото!")
            send_wishlist_menu(message.chat.id)
            return True
        
        bot.send_message(message.chat.id, "❌ Пришлите фото или напишите \"пропустить\".")
        return True
    
    if action == "game_title":
        payload["title"] = message.text.strip()
        set_step(message.from_user.id, "game_draw_date", payload)
        log_action("step_game_title", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "📅 Укажите дату жеребьёвки (например, 25 декабря):")
        return True
    
    if action == "game_draw_date":
        payload["draw_date"] = message.text.strip()
        set_step(message.from_user.id, "game_minimum", payload)
        log_action("step_game_draw_date", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "👥 Минимальное количество участников (рекомендуется 3 или более):")
        return True
    
    if action == "game_minimum":
        try:
            minimum = max(3, int(message.text.strip()))
        except ValueError:
            bot.send_message(message.chat.id, "❌ Введите число не меньше 3.")
            return True
        
        payload["minimum"] = minimum
        game = operations.create_game(
            message.from_user.id, 
            payload.get("title", ""), 
            payload.get("draw_date", ""), 
            minimum
        )
        operations.add_participant(game.id, message.from_user.id)
        pop_step(message.from_user.id)
        log_action("step_game_created", user_id=message.from_user.id, code=game.code)
        
        bot.send_message(
            message.chat.id,
            f"✅ <b>Игра создана успешно!</b>\n\n"
            f"🎄 <b>Название:</b> {game.title}\n"
            f"🔑 <b>Код приглашения:</b> <code>{game.code}</code>\n"
            f"📅 <b>Дата жеребьёвки:</b> {game.draw_date}\n"
            f"👥 <b>Минимум участников:</b> {game.min_participants}\n\n"
            f"Отправьте код <code>{game.code}</code> друзьям, чтобы они присоединились!",
        )
        send_game_menu(message.chat.id)
        return True
    
    if action == "join_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_join_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "❌ Действие отменено.")
            send_main_menu(message.chat.id)
            return True
        
        from bot.handlers.games import join_game_by_code
        if join_game_by_code(message.from_user.id, message.chat.id, code):
            pop_step(message.from_user.id)
            send_main_menu(message.chat.id)
        return True
    
    if action == "leave_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_leave_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "❌ Действие отменено.")
            send_main_menu(message.chat.id)
            return True
        
        from bot.handlers.games import leave_game_by_code
        if leave_game_by_code(message.from_user.id, message.chat.id, code):
            pop_step(message.from_user.id)
            send_main_menu(message.chat.id)
        return True
    
    if action == "participants_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_participants_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "❌ Действие отменено.")
            send_main_menu(message.chat.id)
            return True
        
        from bot.handlers.games import show_participants_by_code
        if show_participants_by_code(message, code):
            pop_step(message.from_user.id)
            send_main_menu(message.chat.id)
        return True
    
    if action == "mix_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_mix_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "❌ Действие отменено.")
            send_main_menu(message.chat.id)
            return True
        
        from bot.handlers.games import mix_game_by_code
        if mix_game_by_code(message, code):
            pop_step(message.from_user.id)
            send_main_menu(message.chat.id)
        return True
    
    if action == "ask_question":
        question = message.text.strip()
        if question.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_ask_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "❌ Действие отменено.")
            send_main_menu(message.chat.id)
            return True
        
        from bot.handlers.games import ask_santa_question
        if ask_santa_question(message.from_user.id, message.chat.id, question):
            pop_step(message.from_user.id)
            send_main_menu(message.chat.id)
        return True
    
    return False