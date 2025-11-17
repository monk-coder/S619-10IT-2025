
"""Secret Santa & Wishlists bot implemented with telebot in a single file."""

from __future__ import annotations

import logging
import os
import random
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException


logger = logging.getLogger("secret_santa_bot")


BOT_TOKEN = BOT_TOKEN = "8592210277:AAFa0JTsmU9pYxq_1dScgNpmDsZSduA9aLw"
if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
    logging.warning("Set TELEGRAM_BOT_TOKEN before running the bot.")

DB_PATH = os.environ.get(
    "SECRET_SANTA_DB",
    os.path.join(os.path.dirname(__file__), "secret_santa.sqlite3"),
)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


DB = get_db()
DB_LOCK = threading.Lock()


def ensure_schema() -> None:
    with DB_LOCK:
        DB.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                bio TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS wish_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                photo_file_id TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                owner_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                draw_date TEXT,
                min_participants INTEGER NOT NULL DEFAULT 3,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS game_participants (
                game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                joined_at REAL NOT NULL,
                PRIMARY KEY (game_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS matches (
                game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                santa_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                recipient_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                PRIMARY KEY (game_id, santa_id)
            );

            CREATE TABLE IF NOT EXISTS anonymous_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                santa_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            """
        )
        DB.commit()


ensure_schema()


bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

bot.set_my_commands(
    [
        types.BotCommand("start", "Запустить бота 🎅"),
        types.BotCommand("help", "Список возможностей 📖"),
        types.BotCommand("menu", "Главное меню 🏠"),
        types.BotCommand("profile", "Показать профиль 👤"),
        types.BotCommand("edit_profile", "Обновить профиль ✏️"),
        types.BotCommand("wishlist", "Мой вишлист 🎁"),
        types.BotCommand("add_item", "Добавить подарок ➕"),
        types.BotCommand("create_game", "Создать игру 🎲"),
        types.BotCommand("status", "Игры, где я организатор 🔔"),
        types.BotCommand("my_recipient", "Мой получатель 🎁"),
    ]
)

BTN_PROFILE = "👤 Профиль"
BTN_EDIT_PROFILE = "✏️ Обновить профиль"
BTN_WISHLIST = "🎁 Мой вишлист"
BTN_ADD_ITEM = "➕ Добавить подарок"
BTN_REMOVE_ITEM = "❌ Удалить подарок"
BTN_CREATE_GAME = "🎲 Создать игру"
BTN_STATUS = "🔔 Мои игры"
BTN_JOIN_GAME = "🎮 Вступить в игру"
BTN_LEAVE_GAME = "🚪 Выйти из игры"
BTN_PARTICIPANTS = "👥 Участники игры"
BTN_MIX = "🎉 Провести жеребьёвку"
BTN_MY_RECIPIENT = "🎁 Кому дарю?"
BTN_MAIN_MENU = "🏠 Главное меню"

MENU_LAYOUT = [
    (BTN_PROFILE, BTN_EDIT_PROFILE),
    (BTN_WISHLIST, BTN_ADD_ITEM),
    (BTN_REMOVE_ITEM,),
    (BTN_CREATE_GAME, BTN_STATUS),
    (BTN_JOIN_GAME, BTN_LEAVE_GAME),
    (BTN_PARTICIPANTS, BTN_MIX),
    (BTN_MY_RECIPIENT, BTN_MAIN_MENU),
]


def build_main_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in MENU_LAYOUT:
        markup.row(*(types.KeyboardButton(title) for title in row))
    return markup


def send_main_menu(chat_id: int, text: str = "Выберите действие 🎄") -> None:
    bot.send_message(chat_id, text, reply_markup=build_main_menu())


def log_action(action: str, **payload: Any) -> None:
    if not payload:
        logger.info(action)
        return
    details = " ".join(f"{key}={value}" for key, value in payload.items())
    logger.info("%s %s", action, details)


pending_steps: Dict[int, Dict[str, Any]] = {}


@dataclass
class Game:
    id: int
    code: str
    owner_id: int
    title: str
    draw_date: Optional[str]
    min_participants: int


def now_ts() -> float:
    return time.time()


def ensure_user(user_id: int, username: Optional[str]) -> None:
    with DB_LOCK:
        row = DB.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            if username:
                DB.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
                DB.commit()
            return
        DB.execute(
            "INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
            (user_id, username, now_ts()),
        )
        DB.commit()


def update_profile(user_id: int, full_name: str, bio: str) -> None:
    with DB_LOCK:
        DB.execute(
            "UPDATE users SET full_name = ?, bio = ? WHERE user_id = ?",
            (full_name, bio, user_id),
        )
        DB.commit()


def get_profile(user_id: int) -> sqlite3.Row:
    with DB_LOCK:
        return DB.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def list_wishlist(user_id: int) -> List[sqlite3.Row]:
    with DB_LOCK:
        return DB.execute(
            "SELECT id, description, photo_file_id FROM wish_items WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()


def add_wish_item(user_id: int, description: str, photo_file_id: Optional[str]) -> None:
    with DB_LOCK:
        DB.execute(
            "INSERT INTO wish_items (user_id, description, photo_file_id, created_at) VALUES (?, ?, ?, ?)",
            (user_id, description.strip(), photo_file_id, now_ts()),
        )
        DB.commit()


def delete_wish_item(user_id: int, item_id: int) -> bool:
    with DB_LOCK:
        cur = DB.execute(
            "DELETE FROM wish_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        )
        DB.commit()
        return cur.rowcount > 0


def generate_game_code() -> str:
    return secrets.token_hex(3).upper()


def create_game(owner_id: int, title: str, draw_date: str, minimum: int) -> Game:
    code = generate_game_code()
    with DB_LOCK:
        DB.execute(
            "INSERT INTO games (code, owner_id, title, draw_date, min_participants, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (code, owner_id, title.strip(), draw_date.strip(), max(3, minimum), now_ts()),
        )
        DB.commit()
        row = DB.execute(
            "SELECT id, code, owner_id, title, draw_date, min_participants FROM games WHERE code = ?",
            (code,),
        ).fetchone()
    return Game(**dict(row))  # type: ignore[arg-type]


def find_game_by_code(code: str) -> Optional[Game]:
    with DB_LOCK:
        row = DB.execute(
            "SELECT id, code, owner_id, title, draw_date, min_participants FROM games WHERE code = ?",
            (code.upper(),),
        ).fetchone()
    return Game(**dict(row)) if row else None  # type: ignore[arg-type]


def add_participant(game_id: int, user_id: int) -> bool:
    with DB_LOCK:
        try:
            DB.execute(
                "INSERT INTO game_participants (game_id, user_id, joined_at) VALUES (?, ?, ?)",
                (game_id, user_id, now_ts()),
            )
            DB.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def remove_participant(game_id: int, user_id: int) -> bool:
    with DB_LOCK:
        if DB.execute("SELECT 1 FROM matches WHERE game_id = ?", (game_id,)).fetchone():
            return False
        cur = DB.execute(
            "DELETE FROM game_participants WHERE game_id = ? AND user_id = ?",
            (game_id, user_id),
        )
        DB.commit()
        return cur.rowcount > 0


def list_participants(game_id: int) -> List[int]:
    with DB_LOCK:
        rows = DB.execute(
            "SELECT user_id FROM game_participants WHERE game_id = ? ORDER BY joined_at",
            (game_id,),
        ).fetchall()
    return [row["user_id"] for row in rows]


def store_matches(game_id: int, pairs: Dict[int, int]) -> None:
    with DB_LOCK:
        DB.execute("DELETE FROM matches WHERE game_id = ?", (game_id,))
        DB.executemany(
            "INSERT INTO matches (game_id, santa_id, recipient_id, created_at) VALUES (?, ?, ?, ?)",
            [(game_id, santa, recipient, now_ts()) for santa, recipient in pairs.items()],
        )
        DB.commit()


def get_match(game_id: int, santa_id: int) -> Optional[int]:
    with DB_LOCK:
        row = DB.execute(
            "SELECT recipient_id FROM matches WHERE game_id = ? AND santa_id = ?",
            (game_id, santa_id),
        ).fetchone()
    return row["recipient_id"] if row else None


def get_games_for_owner(owner_id: int) -> List[Game]:
    with DB_LOCK:
        rows = DB.execute(
            "SELECT id, code, owner_id, title, draw_date, min_participants FROM games WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,),
        ).fetchall()
    return [Game(**dict(row)) for row in rows]  # type: ignore[arg-type]


def get_participating_games(user_id: int) -> List[Game]:
    with DB_LOCK:
        rows = DB.execute(
            """
            SELECT g.id, g.code, g.owner_id, g.title, g.draw_date, g.min_participants
            FROM games g
            JOIN game_participants gp ON gp.game_id = g.id
            WHERE gp.user_id = ?
            ORDER BY g.created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [Game(**dict(row)) for row in rows]  # type: ignore[arg-type]


def format_profile(user_id: int) -> str:
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


def show_profile(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    log_action("show_profile", user_id=message.from_user.id, username=message.from_user.username)
    bot.send_message(message.chat.id, format_profile(message.from_user.id))


def start_profile_edit(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "profile_fullname", {})
    log_action("start_profile_edit", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "✏️ Введите ваше ФИО:")


def build_wishlist_view(user_id: int) -> tuple[str, Optional[types.InlineKeyboardMarkup]]:
    items = list_wishlist(user_id)
    lines = ["<b>🎁 Ваш вишлист:</b>"]
    if not items:
        lines.append("— пока пусто. Нажмите “➕ Добавить подарок”.")
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


def send_wishlist_view(chat_id: int, user_id: int) -> None:
    text, markup = build_wishlist_view(user_id)
    log_action("view_wishlist", user_id=user_id)
    bot.send_message(chat_id, text, reply_markup=markup)


def start_add_item_flow(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "wish_description", {})
    log_action("start_add_item", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "📝 Опишите подарок, который хотите получить:")


def prompt_wishlist_deletion(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    log_action("prompt_remove_item", user_id=message.from_user.id)
    send_wishlist_view(message.chat.id, message.from_user.id)
    bot.send_message(
        message.chat.id,
        "Нажмите кнопку ❌ под списком, чтобы удалить подарок.",
    )


def start_create_game_flow(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "game_title", {})
    log_action("start_create_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎲 Введите название игры:")


def send_owner_status(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    log_action("view_owner_status", user_id=message.from_user.id)
    games = get_games_for_owner(message.from_user.id)
    if not games:
        bot.send_message(message.chat.id, "Пока нет созданных игр. Нажмите “🎲 Создать игру”.")
        return
    lines: List[str] = []
    for game in games:
        participants = list_participants(game.id)
        lines.append(
            f"<b>{game.title}</b> (код <code>{game.code}</code>) — {len(participants)} участника(ов), минимум {game.min_participants}"
        )
        if participants:
            names = []
            for uid in participants:
                profile = get_profile(uid)
                display = profile["full_name"] or profile["username"] or f"ID{uid}"
                names.append(display)
            lines.append("Участники: " + ", ".join(names))
        lines.append("")
    bot.send_message(message.chat.id, "\n".join(line for line in lines if line))


def start_participants_lookup(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "participants_code", {})
    log_action("start_participants_lookup", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "👥 Введите код игры, чтобы увидеть участников:")


def start_join_game(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "join_code", {})
    log_action("start_join_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎮 Введите код игры, чтобы присоединиться:")


def start_leave_game(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "leave_code", {})
    log_action("start_leave_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🚪 Введите код игры, чтобы выйти:")


def start_mix_game(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "mix_code", {})
    log_action("start_mix_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎉 Введите код игры для жеребьёвки:")


def show_my_recipient(message: types.Message) -> None:
    log_action("show_my_recipient", user_id=message.from_user.id)
    games = get_participating_games(message.from_user.id)
    matches: List[str] = []
    for game in games:
        recipient = get_match(game.id, message.from_user.id)
        if not recipient:
            continue
        profile = get_profile(recipient)
        wishlist = list_wishlist(recipient)
        lines = [f"<b>{game.title}</b>"]
        lines.append(f"ФИО: {profile['full_name'] or 'не указано'}")
        lines.append(f"О себе: {profile['bio'] or 'не указано'}")
        if wishlist:
            lines.append("Вишлист:")
            for item in wishlist:
                lines.append(f"• {item['description']}")
        else:
            lines.append("Вишлист пуст.")
        matches.append("\n".join(lines))
    bot.send_message(
        message.chat.id,
        "\n\n".join(matches) if matches else "Пока нет назначенных получателей. Ждите жеребьёвки! 🎁",
    )


def join_game_by_code(user_id: int, chat_id: int, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("join_game_not_found", user_id=user_id, code=code)
        bot.send_message(chat_id, "Игра не найдена. Попробуйте другой код ❗️")
        return False
    added = add_participant(game.id, user_id)
    bot.send_message(
        chat_id,
        "Вы уже участвуете в этой игре." if not added else f"🎉 Вы присоединились к игре <b>{game.title}</b>!",
    )
    log_action("join_game", user_id=user_id, code=code, joined=added)
    return True


def leave_game_by_code(user_id: int, chat_id: int, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("leave_game_not_found", user_id=user_id, code=code)
        bot.send_message(chat_id, "Игра не найдена. Проверьте код.")
        return False
    if remove_participant(game.id, user_id):
        bot.send_message(chat_id, "🚪 Вы вышли из игры.")
        log_action("leave_game", user_id=user_id, code=code, removed=True)
    else:
        bot.send_message(chat_id, "Не удалось выйти. Возможно, жеребьёвка уже проведена.")
        log_action("leave_game_failed", user_id=user_id, code=code)
    return True


def show_participants_by_code(message: types.Message, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("participants_not_found", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Игра не найдена. Попробуйте снова.")
        return False
    if message.from_user.id not in list_participants(game.id) and message.from_user.id != game.owner_id:
        log_action("participants_denied", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Вы не участвуете в этой игре.")
        return True
    participants = list_participants(game.id)
    if not participants:
        log_action("participants_empty", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Пока нет участников.")
        return True
    log_action("participants_list", user_id=message.from_user.id, code=code, count=len(participants))
    lines = [f"<b>{game.title}</b>:"]
    for uid in participants:
        profile = get_profile(uid)
        display = profile["full_name"] or profile["username"] or f"ID{uid}"
        lines.append(display)
    bot.send_message(message.chat.id, "\n".join(lines))
    return True


def mix_game_by_code(message: types.Message, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("mix_not_found", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Игра не найдена. Убедитесь в правильности кода.")
        return False
    if not ensure_owner(message, game):
        return True
    participants = list_participants(game.id)
    if len(participants) < game.min_participants or len(participants) < 3:
        log_action("mix_not_enough", user_id=message.from_user.id, code=code, count=len(participants))
        bot.send_message(message.chat.id, "Недостаточно участников для жеребьёвки.")
        return False
    shuffled = participants[:]
    random.shuffle(shuffled)
    recipients = shuffled[1:] + shuffled[:1]
    pairs = {santa: recipient for santa, recipient in zip(shuffled, recipients)}
    store_matches(game.id, pairs)
    log_action("mix_success", user_id=message.from_user.id, code=code, count=len(participants))
    bot.send_message(message.chat.id, "🎉 Жеребьёвка проведена! Рассылаем результаты участникам.")
    notify_pairs(game, pairs)
    return True


BUTTON_ACTIONS = {
    BTN_PROFILE: show_profile,
    BTN_EDIT_PROFILE: start_profile_edit,
    BTN_WISHLIST: lambda message: send_wishlist_view(message.chat.id, message.from_user.id),
    BTN_ADD_ITEM: start_add_item_flow,
    BTN_REMOVE_ITEM: prompt_wishlist_deletion,
    BTN_CREATE_GAME: start_create_game_flow,
    BTN_STATUS: send_owner_status,
    BTN_JOIN_GAME: start_join_game,
    BTN_LEAVE_GAME: start_leave_game,
    BTN_PARTICIPANTS: start_participants_lookup,
    BTN_MIX: start_mix_game,
    BTN_MY_RECIPIENT: show_my_recipient,
    BTN_MAIN_MENU: lambda message: send_main_menu(message.chat.id, "🏠 Главное меню. Выберите действие:"),
}


def is_main_button(message: types.Message) -> bool:
    return message.content_type == "text" and message.text in BUTTON_ACTIONS


@bot.message_handler(func=is_main_button)
def handle_main_buttons(message: types.Message) -> None:
    action = BUTTON_ACTIONS.get(message.text)
    if action:
        log_action("button_press", user_id=message.from_user.id, button=message.text)
        action(message)


def set_step(user_id: int, action: str, payload: Optional[Dict[str, Any]] = None) -> None:
    pending_steps[user_id] = {"action": action, "payload": payload or {}}


def pop_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.pop(user_id, None)


def get_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.get(user_id)


@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message) -> None:
    user = message.from_user
    ensure_user(user.id, user.username)
    log_action("command_start", user_id=user.id, username=user.username)
    send_main_menu(
        message.chat.id,
        "🎅 Добро пожаловать в Тайного Санту!\nИспользуйте кнопки ниже или /help, чтобы узнать подробности.",
    )


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


def cmd_menu(message: types.Message) -> None:
    log_action("command_menu", user_id=message.from_user.id)
    send_main_menu(message.chat.id, "🏠 Главное меню. Выберите действие:")


@bot.message_handler(commands=["profile"])
def cmd_profile(message: types.Message) -> None:
    show_profile(message)


@bot.message_handler(commands=["edit_profile"])
def cmd_edit_profile(message: types.Message) -> None:
    start_profile_edit(message)


@bot.message_handler(commands=["wishlist"])
def cmd_wishlist(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    log_action("command_wishlist", user_id=message.from_user.id)
    send_wishlist_view(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["add_item"])
def cmd_add_item(message: types.Message) -> None:
    start_add_item_flow(message)


@bot.message_handler(commands=["remove_item"])
def cmd_remove_item(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    log_action("command_remove_item", user_id=message.from_user.id, payload=message.text)
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        prompt_wishlist_deletion(message)
        return
    removed = delete_wish_item(message.from_user.id, int(parts[1]))
    log_action("remove_item_result", user_id=message.from_user.id, item_id=parts[1], removed=removed)
    bot.send_message(message.chat.id, "❌ Подарок удалён." if removed else "Пункт не найден.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_wish:"))
def cb_delete_wish(call: types.CallbackQuery) -> None:
    try:
        item_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        log_action("callback_delete_wish_invalid", user_id=call.from_user.id, data=call.data)
        bot.answer_callback_query(call.id, "Некорректный выбор.", show_alert=True)
        return
    if not delete_wish_item(call.from_user.id, item_id):
        log_action("callback_delete_wish_missing", user_id=call.from_user.id, item_id=item_id)
        bot.answer_callback_query(call.id, "Подарок не найден.", show_alert=True)
        return
    log_action("callback_delete_wish", user_id=call.from_user.id, item_id=item_id)
    text, markup = build_wishlist_view(call.from_user.id)
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
    except ApiTelegramException:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)
    bot.answer_callback_query(call.id, "Удалено ✅")


@bot.message_handler(commands=["create_game"])
def cmd_create_game(message: types.Message) -> None:
    start_create_game_flow(message)


@bot.message_handler(commands=["status"])
def cmd_status(message: types.Message) -> None:
    send_owner_status(message)


@bot.message_handler(commands=["participants"])
def cmd_participants(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_participants_lookup(message)
        return
    ensure_user(message.from_user.id, message.from_user.username)
    show_participants_by_code(message, parts[1])


@bot.message_handler(commands=["join"])
def cmd_join(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_join_game(message)
        return
    ensure_user(message.from_user.id, message.from_user.username)
    join_game_by_code(message.from_user.id, message.chat.id, parts[1])


@bot.message_handler(commands=["leave"])
def cmd_leave(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_leave_game(message)
        return
    ensure_user(message.from_user.id, message.from_user.username)
    leave_game_by_code(message.from_user.id, message.chat.id, parts[1])


def ensure_owner(message: types.Message, game: Game) -> bool:
    if message.from_user.id != game.owner_id:
        log_action("ensure_owner_denied", user_id=message.from_user.id, code=game.code)
        bot.send_message(message.chat.id, "Только организатор может выполнить эту команду.")
        return False
    log_action("ensure_owner_ok", user_id=message.from_user.id, code=game.code)
    return True


@bot.message_handler(commands=["mix", "send"])
def cmd_mix(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_mix_game(message)
        return
    mix_game_by_code(message, parts[1])


def notify_pairs(game: Game, pairs: Dict[int, int]) -> None:
    for santa_id, recipient_id in pairs.items():
        profile = get_profile(recipient_id)
        wishlist = list_wishlist(recipient_id)
        lines = [f"🎅 Вы Тайный Санта в игре <b>{game.title}</b>!", "🎁 Получатель:"]
        lines.append(f"ФИО: {profile['full_name'] or 'не указано'}")
        lines.append(f"О себе: {profile['bio'] or 'не указано'}")
        if wishlist:
            lines.append("🎉 Вишлист:")
            for item in wishlist:
                lines.append(f"• {item['description']}")
        else:
            lines.append("Вишлист пуст.")
        log_action("notify_pair", game_id=game.id, santa_id=santa_id, recipient_id=recipient_id)
        bot.send_message(santa_id, "\n".join(lines))
        for item in wishlist:
            if item["photo_file_id"]:
                bot.send_photo(santa_id, item["photo_file_id"], caption=item["description"])


@bot.message_handler(commands=["my_recipient"])
def cmd_my_recipient(message: types.Message) -> None:
    show_my_recipient(message)


@bot.message_handler(commands=["ask"])
def cmd_ask(message: types.Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        log_action("command_ask_missing", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "Напишите вопрос: /ask Что подарить?")
        return
    question = parts[1].strip()
    log_action("command_ask", user_id=message.from_user.id)
    games = get_participating_games(message.from_user.id)
    sent = 0
    for game in games:
        recipient = get_match(game.id, message.from_user.id)
        if not recipient:
            continue
        profile = get_profile(recipient)
        bot.send_message(
            recipient,
            f"<b>Анонимный вопрос от вашего Санты (игра {game.title}):</b>\n{question}",
        )
        with DB_LOCK:
            DB.execute(
                "INSERT INTO anonymous_questions (game_id, santa_id, recipient_id, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (game.id, message.from_user.id, recipient, question, now_ts()),
            )
            DB.commit()
        sent += 1
    log_action("command_ask_result", user_id=message.from_user.id, sent=sent)
    bot.send_message(message.chat.id, "Вопрос отправлен." if sent else "У вас пока нет получателей.")


def handle_text_step(message: types.Message, step: Dict[str, Any]) -> bool:
    action = step["action"]
    payload = step.get("payload", {})
    if action == "profile_fullname":
        payload["full_name"] = message.text.strip()
        set_step(message.from_user.id, "profile_bio", payload)
        log_action("step_profile_fullname", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "Расскажите о себе (хобби, интересы):")
        return True
    if action == "profile_bio":
        full_name = payload.get("full_name", "")
        update_profile(message.from_user.id, full_name, message.text.strip())
        pop_step(message.from_user.id)
        log_action("step_profile_completed", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "Профиль обновлён.")
        return True
    if action == "wish_description":
        payload["description"] = message.text.strip()
        set_step(message.from_user.id, "wish_photo", payload)
        log_action("step_wish_description", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "Пришлите фото для пожелания или напишите 'пропустить'.")
        return True
    if action == "wish_photo":
        if message.content_type == "text" and message.text.lower() == "пропустить":
            add_wish_item(message.from_user.id, payload.get("description", ""), None)
            pop_step(message.from_user.id)
            log_action("step_wish_photo_skipped", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "Подарок добавлен без фото.")
            return True
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            add_wish_item(message.from_user.id, payload.get("description", ""), file_id)
            pop_step(message.from_user.id)
            log_action("step_wish_photo_uploaded", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "Подарок добавлен с фото.")
            return True
        bot.send_message(message.chat.id, "Пришлите фото или напишите 'пропустить'.")
        return True
    if action == "game_title":
        payload["title"] = message.text.strip()
        set_step(message.from_user.id, "game_draw_date", payload)
        log_action("step_game_title", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "Укажите дату жеребьёвки (например, 24 декабря):")
        return True
    if action == "game_draw_date":
        payload["draw_date"] = message.text.strip()
        set_step(message.from_user.id, "game_minimum", payload)
        log_action("step_game_draw_date", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "Минимальное количество участников (>=3):")
        return True
    if action == "game_minimum":
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
    if action == "join_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_join_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "Действие отменено.")
            return True
        if not code:
            bot.send_message(message.chat.id, "Введите код игры:")
            return True
        if join_game_by_code(message.from_user.id, message.chat.id, code):
            pop_step(message.from_user.id)
        return True
    if action == "leave_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_leave_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "Действие отменено.")
            return True
        if not code:
            bot.send_message(message.chat.id, "Введите код игры:")
            return True
        if leave_game_by_code(message.from_user.id, message.chat.id, code):
            pop_step(message.from_user.id)
        return True
    if action == "participants_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_participants_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "Действие отменено.")
            return True
        if not code:
            bot.send_message(message.chat.id, "Введите код игры:")
            return True
        if show_participants_by_code(message, code):
            pop_step(message.from_user.id)
        return True
    if action == "mix_code":
        code = message.text.strip()
        if code.lower() in {"отмена", "cancel"}:
            pop_step(message.from_user.id)
            log_action("step_mix_cancel", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "Действие отменено.")
            return True
        if not code:
            bot.send_message(message.chat.id, "Введите код игры:")
            return True
        if mix_game_by_code(message, code):
            pop_step(message.from_user.id)
        return True
    return False


@bot.message_handler(content_types=["text", "photo"])
def handle_message(message: types.Message) -> None:
    step = get_step(message.from_user.id)
    if step:
        if handle_text_step(message, step):
            return
    if message.content_type == "text" and not message.text.startswith("/"):
        log_action("unknown_text", user_id=message.from_user.id, text=message.text)
        bot.send_message(message.chat.id, "Не понял команду. Нажмите кнопку в меню или /help.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()