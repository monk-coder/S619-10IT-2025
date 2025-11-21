"""Обработчики главного меню"""
from telebot import types
from database import get_db, DB_LOCK
from utils.keyboards import build_main_menu_keyboard


# Состояния пользователей (временное хранилище)
pending_steps = {}


def ensure_user(message: types.Message) -> None:
    """Создает/обновляет пользователя в БД"""
    user = message.from_user
    with DB_LOCK:
        db = get_db()
        row = db.execute("SELECT 1 FROM users WHERE user_id = ?", (user.id,)).fetchone()
        if row:
            db.execute(
                "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE user_id = ?",
                (user.username, user.first_name, user.last_name, user.id),
            )
        else:
            from utils.helpers import now_ts
            db.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?)",
                (user.id, user.username, user.first_name, user.last_name, now_ts()),
            )
        db.commit()


def set_step(user_id: int, action: str, payload: dict = None) -> None:
    pending_steps[user_id] = {"action": action, "payload": payload or {}}


def pop_step(user_id: int) -> dict:
    return pending_steps.pop(user_id, None)


def get_step(user_id: int) -> dict:
    return pending_steps.get(user_id)


def send_with_main_menu(bot, chat_id: int, text: str, **kwargs):
    """Отправляет сообщение с главным меню"""
    kwargs.setdefault("reply_markup", build_main_menu_keyboard())
    return bot.send_message(chat_id, text, **kwargs)