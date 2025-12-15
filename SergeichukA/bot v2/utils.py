import logging
from typing import Any, Dict, Optional
from telebot import types
from config import MENU_LAYOUT
from bot_instance import bot

logger = logging.getLogger("secret_santa_bot")

def log_action(action: str, **payload: Any) -> None:
    if not payload:
        logger.info(action)
        return
    details = " ".join(f"{key}={value}" for key, value in payload.items())
    logger.info("%s %s", action, details)

def build_main_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in MENU_LAYOUT:
        markup.row(*(types.KeyboardButton(title) for title in row))
    return markup

def send_main_menu(chat_id: int, text: str = "Выберите действие 🎄") -> None:
    bot.send_message(chat_id, text, reply_markup=build_main_menu())

def format_profile(user_id: int) -> str:
    from models import get_profile, list_wishlist
    
    profile = get_profile(user_id)
    if not profile:
        return "Профиль не найден."
    wishlist = list_wishlist(user_id)
    lines = [
        f"<b>ФИО:</b> {profile['full_name'] or 'не указано'}",
        f"<b>О себе:</b> {profile['bio'] or 'не указано'}",
        "<b>Вишлист:</b>",
    ]
    if not wishlist:
        lines.append("— пока пусто")
    else:
        for item in wishlist:
            lines.append(f"• #{item['id']} — {item['description']}")
    return "\n".join(lines)

def build_wishlist_view(user_id: int) -> tuple[str, Optional[types.InlineKeyboardMarkup]]:
    from models import list_wishlist
    
    items = list_wishlist(user_id)
    lines = ["<b>🎁 Ваш вишлист:</b>"]
    if not items:
        lines.append("— пока пусто. Нажмите \"➕ Добавить подарок\".")
        return "\n".join(lines), None
    for item in items:
        lines.append(f"#{item['id']}: {item['description']}")
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in items:
        markup.add(
            types.InlineKeyboardButton(
                text=f"❌ Удалить #{item['id']}", callback_data=f"delete_wish:{item['id']}"
            )
        )
    return "\n".join(lines), markup

# Глобальный словарь для пошаговых действий
pending_steps: Dict[int, Dict[str, Any]] = {}

def set_step(user_id: int, action: str, payload: Optional[Dict[str, Any]] = None) -> None:
    pending_steps[user_id] = {"action": action, "payload": payload or {}}

def pop_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.pop(user_id, None)

def get_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.get(user_id)