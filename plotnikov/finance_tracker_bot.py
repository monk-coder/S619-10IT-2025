#!/usr/bin/env python3
"""Personal finance tracker Telegram bot implemented with telebot in a single file."""

from __future__ import annotations

import csv
import io
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException


MAX_LOG_LEN = 400


def _clip(text: Optional[str]) -> str:
    if text is None:
        return ""
    sanitized = text.replace("\n", "\\n")
    if len(sanitized) <= MAX_LOG_LEN:
        return sanitized
    return sanitized[:MAX_LOG_LEN] + "…"


class LoggingTeleBot(telebot.TeleBot):
    def _log_outbound(self, method: str, payload: Dict[str, Any]) -> None:
        logging.info("-> %s %s", method, payload)

    def send_message(self, chat_id: Any, text: Any, *args: Any, **kwargs: Any) -> Any:
        self._log_outbound("send_message", {"chat_id": chat_id, "text": _clip(str(text))})
        return super().send_message(chat_id, text, *args, **kwargs)

    def edit_message_text(self, text: Any, chat_id: Any, message_id: Any, *args: Any, **kwargs: Any) -> Any:
        self._log_outbound(
            "edit_message_text",
            {"chat_id": chat_id, "message_id": message_id, "text": _clip(str(text))},
        )
        return super().edit_message_text(text, chat_id, message_id, *args, **kwargs)

    def edit_message_reply_markup(self, chat_id: Any, message_id: Any, *args: Any, **kwargs: Any) -> Any:
        self._log_outbound(
            "edit_message_reply_markup",
            {"chat_id": chat_id, "message_id": message_id},
        )
        return super().edit_message_reply_markup(chat_id, message_id, *args, **kwargs)

    def send_document(self, chat_id: Any, document: Any, *args: Any, **kwargs: Any) -> Any:
        name = getattr(document, "name", getattr(document, "filename", "document"))
        self._log_outbound("send_document", {"chat_id": chat_id, "document": name})
        return super().send_document(chat_id, document, *args, **kwargs)

    def send_photo(self, chat_id: Any, photo: Any, *args: Any, **kwargs: Any) -> Any:
        self._log_outbound("send_photo", {"chat_id": chat_id, "photo": str(photo)[:60]})
        return super().send_photo(chat_id, photo, *args, **kwargs)

    def answer_callback_query(self, callback_query_id: Any, text: Optional[str] = None, *args: Any, **kwargs: Any) -> Any:
        self._log_outbound(
            "answer_callback_query",
            {"callback_query_id": callback_query_id, "text": _clip(text) if text else ""},
        )
        return super().answer_callback_query(callback_query_id, text=text, *args, **kwargs)


def log_updates(updates: List[Any]) -> None:
    for update in updates:
        message = getattr(update, "message", None)
        if isinstance(message, types.Message):
            payload = {
                "chat_id": message.chat.id,
                "user_id": message.from_user.id if message.from_user else None,
                "type": message.content_type,
                "text": _clip(message.text if message.content_type == "text" else message.caption),
            }
            logging.info("<- message %s", payload)
        callback = getattr(update, "callback_query", None)
        if isinstance(callback, types.CallbackQuery):
            payload = {
                "chat_id": callback.message.chat.id if callback.message else None,
                "user_id": callback.from_user.id if callback.from_user else None,
                "data": _clip(callback.data),
            }
            logging.info("<- callback %s", payload)


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ВПИШИ ТОКЕН")

DB_PATH = os.environ.get(
    "FINANCE_TRACKER_DB",
    os.path.join(os.path.dirname(__file__), "finance_tracker.sqlite3"),
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
                first_name TEXT,
                last_name TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
                category TEXT,
                amount REAL NOT NULL,
                comment TEXT,
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_user_created_at
                ON transactions(user_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS budgets (
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                PRIMARY KEY (user_id, category)
            );

            CREATE TABLE IF NOT EXISTS budget_alerts (
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                period TEXT NOT NULL,
                threshold TEXT NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(user_id, category, period, threshold)
            );
            """
        )
        DB.commit()


ensure_schema()


EXPENSE_CATEGORIES: Tuple[Tuple[str, str, str], ...] = (
    ("food", "🍔", "Еда"),
    ("transport", "🚌", "Транспорт"),
    ("entertainment", "🎮", "Развлечения"),
    ("housing", "🏠", "Жильё"),
    ("education", "📚", "Учёба"),
    ("health", "💊", "Здоровье"),
    ("clothes", "👕", "Одежда"),
    ("communication", "📱", "Связь"),
    ("other", "✨", "Другое"),
)


CATEGORY_INFO: Dict[str, Tuple[str, str]] = {
    key: (emoji, title) for key, emoji, title in EXPENSE_CATEGORIES
}


CATEGORY_ALIASES: Dict[str, str] = {}
for key, emoji, title in EXPENSE_CATEGORIES:
    CATEGORY_ALIASES[key] = key
    CATEGORY_ALIASES[emoji] = key
    CATEGORY_ALIASES[title.lower()] = key
    CATEGORY_ALIASES[title.lower().replace("ё", "е")] = key


MAIN_MENU_LAYOUT: Tuple[Tuple[str, ...], ...] = (
    ("➕ Расход", "💰 Доход"),
    ("📊 Сегодня", "📈 Неделя", "🗓️ Месяц"),
    ("📰 История", "🎯 Бюджеты"),
)


def build_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in MAIN_MENU_LAYOUT:
        markup.row(*(types.KeyboardButton(btn) for btn in row))
    return markup


def send_with_main_menu(chat_id: int, text: str, **kwargs: Any) -> Any:
    kwargs.setdefault("reply_markup", build_main_menu_keyboard())
    return bot.send_message(chat_id, text, **kwargs)


bot = LoggingTeleBot(BOT_TOKEN, parse_mode="HTML")
bot.set_update_listener(log_updates)

bot.set_my_commands(
    [
        types.BotCommand("start", "Начать работу"),
        types.BotCommand("help", "Справка"),
        types.BotCommand("add", "Добавить расход"),
        types.BotCommand("income", "Добавить доход"),
        types.BotCommand("today", "Статистика за сегодня"),
        types.BotCommand("week", "Статистика за 7 дней"),
        types.BotCommand("month", "Статистика за месяц"),
        types.BotCommand("history", "История транзакций"),
        types.BotCommand("set_budget", "Установить бюджет"),
        types.BotCommand("goals", "Прогресс по бюджетам"),
        types.BotCommand("export", "Экспорт CSV"),
    ]
)


pending_steps: Dict[int, Dict[str, Any]] = {}


def now_ts() -> float:
    return time.time()


def ensure_user(message: types.Message) -> None:
    user = message.from_user
    with DB_LOCK:
        row = DB.execute("SELECT 1 FROM users WHERE user_id = ?", (user.id,)).fetchone()
        if row:
            DB.execute(
                "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE user_id = ?",
                (user.username, user.first_name, user.last_name, user.id),
            )
        else:
            DB.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?)",
                (user.id, user.username, user.first_name, user.last_name, now_ts()),
            )
        DB.commit()


def set_step(user_id: int, action: str, payload: Optional[Dict[str, Any]] = None) -> None:
    pending_steps[user_id] = {"action": action, "payload": payload or {}}


def pop_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.pop(user_id, None)


def get_step(user_id: int) -> Optional[Dict[str, Any]]:
    return pending_steps.get(user_id)


def parse_amount(value: str) -> float:
    normalized = value.replace(" ", "").replace(",", ".")
    amount = float(normalized)
    if amount <= 0:
        raise ValueError("amount must be positive")
    return round(amount, 2)


def insert_transaction(user_id: int, tx_type: str, category: Optional[str], amount: float, comment: Optional[str]) -> int:
    with DB_LOCK:
        cur = DB.execute(
            "INSERT INTO transactions (user_id, type, category, amount, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, tx_type, category, amount, comment, now_ts()),
        )
        DB.commit()
        return cur.lastrowid


def delete_transaction(user_id: int, tx_id: int) -> bool:
    with DB_LOCK:
        cur = DB.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
        DB.commit()
        return cur.rowcount > 0


def fetch_transactions(user_id: int, start_ts: Optional[float], end_ts: Optional[float], tx_type: Optional[str] = None) -> List[sqlite3.Row]:
    query = ["SELECT id, type, category, amount, comment, created_at FROM transactions WHERE user_id = ?"]
    params: List[Any] = [user_id]
    if tx_type:
        query.append("AND type = ?")
        params.append(tx_type)
    if start_ts is not None:
        query.append("AND created_at >= ?")
        params.append(start_ts)
    if end_ts is not None:
        query.append("AND created_at <= ?")
        params.append(end_ts)
    query.append("ORDER BY created_at DESC")
    with DB_LOCK:
        return DB.execute(" ".join(query), tuple(params)).fetchall()


def fetch_recent_transactions(user_id: int, limit: int = 10) -> List[sqlite3.Row]:
    with DB_LOCK:
        return DB.execute(
            "SELECT id, type, category, amount, comment, created_at FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()


def upsert_budget(user_id: int, category: str, amount: float) -> None:
    with DB_LOCK:
        DB.execute(
            "INSERT INTO budgets (user_id, category, amount) VALUES (?, ?, ?) ON CONFLICT(user_id, category) DO UPDATE SET amount = excluded.amount",
            (user_id, category, amount),
        )
        DB.commit()


def fetch_budgets(user_id: int) -> List[sqlite3.Row]:
    with DB_LOCK:
        return DB.execute("SELECT category, amount FROM budgets WHERE user_id = ?", (user_id,)).fetchall()


def get_budget(user_id: int, category: str) -> Optional[float]:
    with DB_LOCK:
        row = DB.execute("SELECT amount FROM budgets WHERE user_id = ? AND category = ?", (user_id, category)).fetchone()
    return row["amount"] if row else None


def budget_alert_sent(user_id: int, category: str, period: str, threshold: str) -> bool:
    with DB_LOCK:
        row = DB.execute(
            "SELECT 1 FROM budget_alerts WHERE user_id = ? AND category = ? AND period = ? AND threshold = ?",
            (user_id, category, period, threshold),
        ).fetchone()
    return bool(row)


def mark_budget_alert(user_id: int, category: str, period: str, threshold: str) -> None:
    with DB_LOCK:
        DB.execute(
            "INSERT OR IGNORE INTO budget_alerts (user_id, category, period, threshold, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, period, threshold, now_ts()),
        )
        DB.commit()


def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999000)


def month_bounds(dt: datetime) -> Tuple[datetime, datetime]:
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if dt.month == 12:
        end_month = start.replace(year=dt.year + 1, month=1)
    else:
        end_month = start.replace(month=dt.month + 1)
    end = end_month - timedelta(microseconds=1000)
    return start, end


def aggregate_by_category(rows: Iterable[sqlite3.Row]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for row in rows:
        category = row["category"] or "other"
        totals[category] = totals.get(category, 0.0) + float(row["amount"])
    return totals


def render_bar(percent: float) -> str:
    if percent <= 0:
        return ""
    blocks = max(1, int(percent // 5))
    return "█" * min(blocks, 20)


def format_category_line(category: str, amount: float, percent: float) -> str:
    emoji, title = CATEGORY_INFO.get(category, ("✨", category.capitalize()))
    bar = render_bar(percent)
    return f"{emoji} {title}: {amount:.2f}₽ {bar} {percent:.0f}%"


def summarize_period(message: types.Message, label: str, start_ts: float, end_ts: float) -> None:
    rows = fetch_transactions(message.from_user.id, start_ts, end_ts, tx_type="expense")
    if not rows:
        send_with_main_menu(message.chat.id, f"Нет расходов за {label}.")
        return
    totals = aggregate_by_category(rows)
    total_amount = sum(totals.values())
    lines = [f"<b>Расходы за {label}</b>"]
    for category, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        percent = (amount / total_amount) * 100 if total_amount else 0
        lines.append(format_category_line(category, amount, percent))
    if label == "месяц":
        days_in_period = max(1, (datetime.fromtimestamp(end_ts) - datetime.fromtimestamp(start_ts)).days + 1)
        avg = total_amount / days_in_period
        lines.append("")
        lines.append(f"Итого: {total_amount:.2f}₽")
        lines.append(f"Средний расход в день: {avg:.2f}₽")
    send_with_main_menu(message.chat.id, "\n".join(lines))


def check_budget_thresholds(user_id: int, category: str, chat_id: int) -> None:
    budget = get_budget(user_id, category)
    if not budget:
        return
    emoji, title = CATEGORY_INFO.get(category, ("✨", category))
    now = datetime.now()
    start, end = month_bounds(now)
    rows = fetch_transactions(user_id, start.timestamp(), end.timestamp(), tx_type="expense")
    spent = sum(float(row["amount"]) for row in rows if row["category"] == category)
    if spent <= 0:
        return
    period = start.strftime("%Y-%m")
    for threshold_value, threshold_name in ((0.8, "80"), (1.0, "100")):
        if spent >= budget * threshold_value and not budget_alert_sent(user_id, category, period, threshold_name):
            mark_budget_alert(user_id, category, period, threshold_name)
            percent = min(100, (spent / budget) * 100)
            bot.send_message(
                chat_id,
                f"⚠️ {emoji} {title}: израсходовано {spent:.2f}₽ ({percent:.0f}% от бюджета {budget:.2f}₽)",
            )


def build_categories_keyboard(action: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons: List[types.InlineKeyboardButton] = []
    for key, emoji, title in EXPENSE_CATEGORIES:
        buttons.append(types.InlineKeyboardButton(text=f"{emoji} {title}", callback_data=f"{action}:{key}"))
    while buttons:
        row = buttons[:3]
        buttons = buttons[3:]
        markup.row(*row)
    return markup


def refresh_history_message(user_id: int, chat_id: int, message_id: int) -> None:
    rows = fetch_recent_transactions(user_id)
    text, markup = build_history_view(rows)
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")


def build_history_view(rows: Iterable[sqlite3.Row]) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    lines = ["<b>Последние операции</b>"]
    markup = types.InlineKeyboardMarkup(row_width=1) if rows else None
    for row in rows:
        dt = datetime.fromtimestamp(row["created_at"]).strftime("%d.%m %H:%M")
        amount = float(row["amount"])
        if row["type"] == "expense":
            emoji, title = CATEGORY_INFO.get(row["category"], ("✨", row["category"] or "Другое"))
            prefix = "-"
            category_text = f"{emoji} {title}"
        else:
            prefix = "+"
            category_text = f"💰 {row['category'] or 'Доход'}"
        comment = row["comment"] or ""
        comment_suffix = f" — {comment}" if comment else ""
        lines.append(f"{dt} • {category_text} • {prefix}{amount:.2f}₽{comment_suffix}")
        if markup:
            markup.add(
                types.InlineKeyboardButton(
                    text=f"Удалить {int(row['id'])}",
                    callback_data=f"delete_tx:{int(row['id'])}",
                )
            )
    if len(lines) == 1:
        lines.append("Записей пока нет.")
    return "\n".join(lines), markup


def start_expense_flow(message: types.Message) -> None:
    ensure_user(message)
    markup = build_categories_keyboard("add_expense")
    bot.send_message(
        message.chat.id,
        "<b>Добавление расхода</b>\n1. Выберите категорию ниже.\n2. Введите сумму (например, 450).\n3. Добавьте комментарий при необходимости.",
        reply_markup=markup,
    )


def start_income_flow(message: types.Message) -> None:
    ensure_user(message)
    set_step(message.from_user.id, "income_amount", {})
    bot.send_message(
        message.chat.id,
        "<b>Добавление дохода</b>\nВведите сумму (например, 2500), затем укажите источник дохода.",
        reply_markup=build_main_menu_keyboard(),
    )


def show_today_stats(message: types.Message) -> None:
    ensure_user(message)
    today = datetime.now()
    start = start_of_day(today).timestamp()
    end = end_of_day(today).timestamp()
    summarize_period(message, "сегодня", start, end)


def show_week_stats(message: types.Message) -> None:
    ensure_user(message)
    today = datetime.now()
    start = start_of_day(today - timedelta(days=6)).timestamp()
    end = end_of_day(today).timestamp()
    summarize_period(message, "неделю", start, end)


def show_month_stats(message: types.Message) -> None:
    ensure_user(message)
    now = datetime.now()
    start, end = month_bounds(now)
    summarize_period(message, "месяц", start.timestamp(), end.timestamp())


def show_history(message: types.Message) -> None:
    ensure_user(message)
    rows = fetch_recent_transactions(message.from_user.id)
    text, markup = build_history_view(rows)
    bot.send_message(message.chat.id, text, reply_markup=markup)


def show_goals(message: types.Message) -> None:
    ensure_user(message)
    budgets = fetch_budgets(message.from_user.id)
    if not budgets:
        send_with_main_menu(message.chat.id, "Бюджеты не заданы. Используйте /set_budget.")
        return
    now = datetime.now()
    start, end = month_bounds(now)
    rows = fetch_transactions(message.from_user.id, start.timestamp(), end.timestamp(), tx_type="expense")
    spent_by_category = aggregate_by_category(rows)
    lines = ["<b>Прогресс по бюджетам</b>"]
    for row in budgets:
        category = row["category"]
        budget_amount = float(row["amount"])
        spent = spent_by_category.get(category, 0.0)
        percent = min(100, (spent / budget_amount) * 100) if budget_amount else 0
        emoji, title = CATEGORY_INFO.get(category, ("✨", category))
        lines.append(f"{emoji} {title}: {spent:.2f}/{budget_amount:.2f}₽ ({percent:.0f}%)")
    send_with_main_menu(message.chat.id, "\n".join(lines))


MAIN_MENU_ACTIONS: Dict[str, Any] = {
    "➕ Расход": start_expense_flow,
    "💰 Доход": start_income_flow,
    "📊 Сегодня": show_today_stats,
    "📈 Неделя": show_week_stats,
    "🗓️ Месяц": show_month_stats,
    "📰 История": show_history,
    "🎯 Бюджеты": show_goals,
}


@bot.message_handler(func=lambda message: message.content_type == "text" and message.text in MAIN_MENU_ACTIONS)
def handle_main_menu_buttons(message: types.Message) -> None:
    pop_step(message.from_user.id)
    action = MAIN_MENU_ACTIONS.get(message.text)
    if action:
        action(message)


SKIP_COMMENT_CALLBACK = "skip_comment"


def build_comment_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Пропустить 💨", callback_data=SKIP_COMMENT_CALLBACK))
    return markup


@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message) -> None:
    ensure_user(message)
    send_with_main_menu(
        message.chat.id,
        "<b>Добро пожаловать!</b>\nЯ помогу быстро записывать расходы и доходы, показывать статистику и следить за бюджетами.\n\nВыбирайте кнопки ниже или используйте команды из /help.",
    )


@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message) -> None:
    ensure_user(message)
    send_with_main_menu(
        message.chat.id,
        """<b>Основные команды</b>
/add — добавить расход через клавиатуру категорий
/income — записать доход
/today — статистика за сегодня
/week — статистика за последние 7 дней
/month — статистика за текущий месяц
/history — последние операции и удаление
/set_budget категория сумма — установить лимит (/set_budget еда 5000)
/goals — прогресс по лимитам
/export YYYY-MM — выгрузка CSV за месяц
""",
    )


@bot.message_handler(commands=["add"])
def cmd_add(message: types.Message) -> None:
    start_expense_flow(message)


@bot.message_handler(commands=["income"])
def cmd_income(message: types.Message) -> None:
    start_income_flow(message)


@bot.message_handler(commands=["today"])
def cmd_today(message: types.Message) -> None:
    show_today_stats(message)


@bot.message_handler(commands=["week"])
def cmd_week(message: types.Message) -> None:
    show_week_stats(message)


@bot.message_handler(commands=["month"])
def cmd_month(message: types.Message) -> None:
    show_month_stats(message)


@bot.message_handler(commands=["history"])
def cmd_history(message: types.Message) -> None:
    show_history(message)


def resolve_category(name: str) -> Optional[str]:
    key = CATEGORY_ALIASES.get(name.lower())
    return key


@bot.message_handler(commands=["set_budget"])
def cmd_set_budget(message: types.Message) -> None:
    ensure_user(message)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        send_with_main_menu(
            message.chat.id,
            "Использование: /set_budget категория сумма\nНапример: /set_budget еда 5000",
        )
        return
    category = resolve_category(parts[1])
    if not category:
        send_with_main_menu(message.chat.id, "Неизвестная категория. Используйте названия из /add.")
        return
    try:
        amount = parse_amount(parts[2])
    except ValueError:
        send_with_main_menu(message.chat.id, "Сумма должна быть положительным числом.")
        return
    upsert_budget(message.from_user.id, category, amount)
    emoji, title = CATEGORY_INFO.get(category, ("✨", category))
    send_with_main_menu(message.chat.id, f"Бюджет для {emoji} {title} установлен на {amount:.2f}₽")


@bot.message_handler(commands=["goals"])
def cmd_goals(message: types.Message) -> None:
    show_goals(message)


@bot.message_handler(commands=["export"])
def cmd_export(message: types.Message) -> None:
    ensure_user(message)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_main_menu(message.chat.id, "Использование: /export YYYY-MM")
        return
    try:
        period = datetime.strptime(parts[1].strip(), "%Y-%m")
    except ValueError:
        send_with_main_menu(message.chat.id, "Неверный формат. Используйте YYYY-MM, например 2025-01.")
        return
    start, end = month_bounds(period)
    rows = fetch_transactions(message.from_user.id, start.timestamp(), end.timestamp(), tx_type=None)
    if not rows:
        send_with_main_menu(message.chat.id, "За выбранный месяц нет операций.")
        return
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "type", "category", "amount", "comment", "created_at"])
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["type"],
                row["category"] or "",
                f"{float(row['amount']):.2f}",
                row["comment"] or "",
                datetime.fromtimestamp(row["created_at"]).isoformat(sep=" ", timespec="minutes"),
            ]
        )
    buffer.seek(0)
    filename = f"finance_{message.from_user.id}_{start.strftime('%Y_%m')}.csv"
    binary = io.BytesIO(buffer.getvalue().encode("utf-8"))
    binary.name = filename
    bot.send_document(message.chat.id, binary)


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_expense:"))
def cb_add_expense(call: types.CallbackQuery) -> None:
    category = call.data.split(":", 1)[1]
    emoji, title = CATEGORY_INFO.get(category, ("✨", category))
    set_step(call.from_user.id, "expense_amount", {"category": category, "message_id": call.message.message_id, "chat_id": call.message.chat.id})
    bot.answer_callback_query(call.id, text=f"Категория: {title}")
    bot.send_message(call.message.chat.id, f"Введите сумму для {emoji} {title}:")


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_tx:"))
def cb_delete_transaction(call: types.CallbackQuery) -> None:
    try:
        tx_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "Некорректный запрос.", show_alert=True)
        return
    if delete_transaction(call.from_user.id, tx_id):
        bot.answer_callback_query(call.id, "Запись удалена ✅")
        try:
            refresh_history_message(call.from_user.id, call.message.chat.id, call.message.message_id)
        except ApiTelegramException:
            rows = fetch_recent_transactions(call.from_user.id)
            text, markup = build_history_view(rows)
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "Не удалось удалить.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == SKIP_COMMENT_CALLBACK)
def cb_skip_comment(call: types.CallbackQuery) -> None:
    step = get_step(call.from_user.id)
    if not step or step.get("action") != "expense_comment":
        bot.answer_callback_query(call.id, "Нет ожидаемого комментария.", show_alert=True)
        return
    payload = step.get("payload", {})
    finalize_expense_entry(call.from_user.id, call.message.chat.id, payload, "")
    bot.answer_callback_query(call.id, "Комментарий пропущен")


def handle_expense_amount(message: types.Message, payload: Dict[str, Any]) -> bool:
    try:
        amount = parse_amount(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "Сумма должна быть положительным числом. Попробуйте снова:")
        return True
    payload["amount"] = amount
    prompt = bot.send_message(
        message.chat.id,
        "Добавьте комментарий или нажмите кнопку, чтобы пропустить.",
        reply_markup=build_comment_keyboard(),
    )
    payload["comment_prompt_id"] = prompt.message_id
    set_step(message.from_user.id, "expense_comment", payload)
    return True


def finalize_expense_entry(user_id: int, chat_id: int, payload: Dict[str, Any], comment: Optional[str]) -> None:
    prompt_id = payload.get("comment_prompt_id")
    if prompt_id:
        try:
            bot.edit_message_reply_markup(chat_id, prompt_id)
        except ApiTelegramException:
            pass
    insert_transaction(user_id, "expense", payload.get("category"), payload.get("amount", 0.0), (comment or "") or None)
    pop_step(user_id)
    emoji, title = CATEGORY_INFO.get(payload.get("category", "other"), ("✨", "Расход"))
    send_with_main_menu(
        chat_id,
        f"Записано: {emoji} {title} — {payload.get('amount', 0.0):.2f}₽",
    )
    check_budget_thresholds(user_id, payload.get("category", "other"), chat_id)


def handle_expense_comment(message: types.Message, payload: Dict[str, Any]) -> bool:
    comment = message.text.strip()
    finalize_expense_entry(message.from_user.id, message.chat.id, payload, comment)
    return True


def handle_income_amount(message: types.Message, payload: Dict[str, Any]) -> bool:
    try:
        amount = parse_amount(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "Сумма должна быть положительным числом. Попробуйте снова:")
        return True
    payload["amount"] = amount
    set_step(message.from_user.id, "income_source", payload)
    bot.send_message(message.chat.id, "Укажите источник дохода (например, стипендия):")
    return True


def handle_income_source(message: types.Message, payload: Dict[str, Any]) -> bool:
    source = message.text.strip() or "Доход"
    insert_transaction(message.from_user.id, "income", source, payload.get("amount", 0.0), None)
    pop_step(message.from_user.id)
    send_with_main_menu(
        message.chat.id,
        f"Доход {source} на сумму {payload.get('amount', 0.0):.2f}₽ добавлен.",
    )
    return True


@bot.message_handler(content_types=["text"])
def handle_text(message: types.Message) -> None:
    step = get_step(message.from_user.id)
    if step:
        action = step.get("action")
        payload = step.get("payload", {})
        if action == "expense_amount":
            if handle_expense_amount(message, payload):
                return
        elif action == "expense_comment":
            if handle_expense_comment(message, payload):
                return
        elif action == "income_amount":
            if handle_income_amount(message, payload):
                return
        elif action == "income_source":
            if handle_income_source(message, payload):
                return
    if message.text.startswith("/"):
        return
    send_with_main_menu(message.chat.id, "Выберите действие через кнопки ниже или используйте /help.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
