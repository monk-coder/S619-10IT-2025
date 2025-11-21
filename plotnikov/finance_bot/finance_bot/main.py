"""Главный файл бота"""
import logging
import io
import csv
from datetime import datetime

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

from config import BOT_TOKEN
from utils.helpers import clip
from utils.keyboards import build_main_menu_keyboard, SKIP_COMMENT_CALLBACK
from handlers.main_menu import (
    ensure_user, set_step, get_step, pop_step, send_with_main_menu,
    pending_steps
)
from handlers.transactions import (
    start_expense_flow, start_income_flow, handle_expense_amount, 
    handle_expense_comment, finalize_expense_entry, delete_transaction,
    fetch_recent_transactions, insert_transaction, handle_income_amount,
    handle_income_source
)
from handlers.stats import (
    show_today_stats, show_week_stats, show_month_stats, show_history,
    build_history_view, refresh_history_message
)
from handlers.budgets import show_goals, upsert_budget, resolve_category
from utils.helpers import CATEGORY_INFO, parse_amount


class LoggingTeleBot(telebot.TeleBot):
    """Бот с логированием"""
    def _log_outbound(self, method: str, payload: dict) -> None:
        logging.info("-> %s %s", method, payload)

    def send_message(self, chat_id, text, *args, **kwargs):
        self._log_outbound("send_message", {"chat_id": chat_id, "text": clip(str(text))})
        return super().send_message(chat_id, text, *args, **kwargs)

    def edit_message_text(self, text, chat_id, message_id, *args, **kwargs):
        self._log_outbound("edit_message_text", {
            "chat_id": chat_id, 
            "message_id": message_id, 
            "text": clip(str(text))
        })
        return super().edit_message_text(text, chat_id, message_id, *args, **kwargs)

    def answer_callback_query(self, callback_query_id, text=None, *args, **kwargs):
        self._log_outbound("answer_callback_query", {
            "callback_query_id": callback_query_id,
            "text": clip(text) if text else ""
        })
        return super().answer_callback_query(callback_query_id, text=text, *args, **kwargs)


# Инициализация бота
bot = LoggingTeleBot(BOT_TOKEN, parse_mode="HTML")


def log_updates(updates):
    """Логирование входящих сообщений"""
    for update in updates:
        message = getattr(update, "message", None)
        if isinstance(message, types.Message):
            payload = {
                "chat_id": message.chat.id,
                "user_id": message.from_user.id if message.from_user else None,
                "type": message.content_type,
                "text": clip(message.text if message.content_type == "text" else message.caption),
            }
            logging.info("<- message %s", payload)
        callback = getattr(update, "callback_query", None)
        if isinstance(callback, types.CallbackQuery):
            payload = {
                "chat_id": callback.message.chat.id if callback.message else None,
                "user_id": callback.from_user.id if callback.from_user else None,
                "data": clip(callback.data),
            }
            logging.info("<- callback %s", payload)


bot.set_update_listener(log_updates)

# Регистрация команд бота
bot.set_my_commands([
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
])

# Главное меню действий
MAIN_MENU_ACTIONS = {
    "➕ Расход": start_expense_flow,
    "💰 Доход": start_income_flow,
    "📊 Сегодня": show_today_stats,
    "📈 Неделя": show_week_stats,
    "🗓️ Месяц": show_month_stats,
    "📰 История": show_history,
    "🎯 Бюджеты": show_goals,
}


# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    ensure_user(message)
    send_with_main_menu(
        bot,
        message.chat.id,
        "<b>Добро пожаловать!</b>\nЯ помогу быстро записывать расходы и доходы, "
        "показывать статистику и следить за бюджетами.\n\n"
        "Выбирайте кнопки ниже или используйте команды из /help."
    )


@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message):
    ensure_user(message)
    send_with_main_menu(bot, message.chat.id, 
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
"""
    )


@bot.message_handler(commands=["add"])
def cmd_add(message: types.Message):
    start_expense_flow(bot, message)


@bot.message_handler(commands=["income"])
def cmd_income(message: types.Message):
    start_income_flow(bot, message)


@bot.message_handler(commands=["today"])
def cmd_today(message: types.Message):
    show_today_stats(bot, message)


@bot.message_handler(commands=["week"])
def cmd_week(message: types.Message):
    show_week_stats(bot, message)


@bot.message_handler(commands=["month"])
def cmd_month(message: types.Message):
    show_month_stats(bot, message)


@bot.message_handler(commands=["history"])
def cmd_history(message: types.Message):
    show_history(bot, message)


@bot.message_handler(commands=["set_budget"])
def cmd_set_budget(message: types.Message):
    ensure_user(message)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        send_with_main_menu(bot, message.chat.id,
            "Использование: /set_budget категория сумма\nПример: /set_budget еда 5000")
        return
        
    category = resolve_category(parts[1])
    if not category:
        send_with_main_menu(bot, message.chat.id, "Неизвестная категория. Используйте названия из /add.")
        return
        
    try:
        amount = parse_amount(parts[2])
    except ValueError:
        send_with_main_menu(bot, message.chat.id, "Сумма должна быть положительным числом.")
        return
        
    upsert_budget(message.from_user.id, category, amount)
    emoji, title = CATEGORY_INFO.get(category, ("✨", category))
    send_with_main_menu(bot, message.chat.id, 
        f"Бюджет для {emoji} {title} установлен на {amount:.2f}₽")


@bot.message_handler(commands=["goals"])
def cmd_goals(message: types.Message):
    show_goals(bot, message)


@bot.message_handler(commands=["export"])
def cmd_export(message: types.Message):
    ensure_user(message)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_main_menu(bot, message.chat.id, "Использование: /export YYYY-MM")
        return
        
    try:
        period = datetime.strptime(parts[1].strip(), "%Y-%m")
    except ValueError:
        send_with_main_menu(bot, message.chat.id, "Неверный формат. Используйте YYYY-MM, например 2025-01.")
        return
        
    start, end = month_bounds(period)
    rows = fetch_transactions(message.from_user.id, start.timestamp(), end.timestamp(), tx_type=None)
    
    if not rows:
        send_with_main_menu(bot, message.chat.id, "За выбранный месяц нет операций.")
        return
        
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "type", "category", "amount", "comment", "created_at"])
    
    for row in rows:
        writer.writerow([
            row["id"],
            row["type"],
            row["category"] or "",
            f"{float(row['amount']):.2f}",
            row["comment"] or "",
            datetime.fromtimestamp(row["created_at"]).isoformat(sep=" ", timespec="minutes"),
        ])
        
    buffer.seek(0)
    filename = f"finance_{message.from_user.id}_{start.strftime('%Y_%m')}.csv"
    binary = io.BytesIO(buffer.getvalue().encode("utf-8"))
    binary.name = filename
    bot.send_document(message.chat.id, binary)


# ========== ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ ==========

@bot.message_handler(func=lambda message: message.content_type == "text" and message.text in MAIN_MENU_ACTIONS)
def handle_main_menu_buttons(message: types.Message):
    pop_step(message.from_user.id)
    action = MAIN_MENU_ACTIONS.get(message.text)
    if action:
        action(bot, message)


# ========== ОБРАБОТЧИКИ CALLBACK QUERY ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_expense:"))
def cb_add_expense(call: types.CallbackQuery):
    category = call.data.split(":", 1)[1]
    emoji, title = CATEGORY_INFO.get(category, ("✨", category))
    set_step(call.from_user.id, "expense_amount", {
        "category": category, 
        "message_id": call.message.message_id, 
        "chat_id": call.message.chat.id
    })
    bot.answer_callback_query(call.id, text=f"Категория: {title}")
    bot.send_message(call.message.chat.id, f"Введите сумму для {emoji} {title}:")


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_tx:"))
def cb_delete_transaction(call: types.CallbackQuery):
    try:
        tx_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "Некорректный запрос.", show_alert=True)
        return
        
    if delete_transaction(call.from_user.id, tx_id):
        bot.answer_callback_query(call.id, "Запись удалена ✅")
        refresh_history_message(bot, call.from_user.id, call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Не удалось удалить.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == SKIP_COMMENT_CALLBACK)
def cb_skip_comment(call: types.CallbackQuery):
    step = get_step(call.from_user.id)
    if not step or step.get("action") != "expense_comment":
        bot.answer_callback_query(call.id, "Нет ожидаемого комментария.", show_alert=True)
        return
        
    payload = step.get("payload", {})
    finalize_expense_entry(bot, call.from_user.id, call.message.chat.id, payload, "")
    bot.answer_callback_query(call.id, "Комментарий пропущен")


# ========== ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ ==========

@bot.message_handler(content_types=["text"])
def handle_text(message: types.Message):
    step = get_step(message.from_user.id)
    if step:
        action = step.get("action")
        payload = step.get("payload", {})
        
        if action == "expense_amount":
            if handle_expense_amount(bot, message, payload):
                return
        elif action == "expense_comment":
            if handle_expense_comment(bot, message, payload):
                return
        elif action == "income_amount":
            if handle_income_amount(bot, message, payload):
                return
        elif action == "income_source":
            if handle_income_source(bot, message, payload):
                return
                
    if message.text.startswith("/"):
        return
        
    send_with_main_menu(bot, message.chat.id, "Выберите действие через кнопки ниже или используйте /help.")


# ========== ЗАПУСК БОТА ==========

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s"
    )
    print("Бот запускается...")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()