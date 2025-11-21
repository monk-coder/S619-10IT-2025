"""Статистика и отчеты"""
from datetime import datetime, timedelta
from telebot import types
from utils.helpers import start_of_day, end_of_day, month_bounds, aggregate_by_category, format_category_line
from handlers.transactions import fetch_transactions
from handlers.main_menu import send_with_main_menu


def summarize_period(bot, message: types.Message, label: str, start_ts: float, end_ts: float):
    rows = fetch_transactions(message.from_user.id, start_ts, end_ts, tx_type="expense")
    if not rows:
        send_with_main_menu(bot, message.chat.id, f"Нет расходов за {label}.")
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
        
    send_with_main_menu(bot, message.chat.id, "\n".join(lines))


def show_today_stats(bot, message: types.Message):
    today = datetime.now()
    start = start_of_day(today).timestamp()
    end = end_of_day(today).timestamp()
    summarize_period(bot, message, "сегодня", start, end)


def show_week_stats(bot, message: types.Message):
    today = datetime.now()
    start = start_of_day(today - timedelta(days=6)).timestamp()
    end = end_of_day(today).timestamp()
    summarize_period(bot, message, "неделю", start, end)


def show_month_stats(bot, message: types.Message):
    now = datetime.now()
    start, end = month_bounds(now)
    summarize_period(bot, message, "месяц", start.timestamp(), end.timestamp())


def build_history_view(rows):
    from utils.helpers import CATEGORY_INFO
    from telebot import types
    
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


def show_history(bot, message: types.Message):
    from handlers.main_menu import ensure_user
    ensure_user(message)
    rows = fetch_recent_transactions(message.from_user.id)
    text, markup = build_history_view(rows)
    bot.send_message(message.chat.id, text, reply_markup=markup)


def refresh_history_message(bot, user_id: int, chat_id: int, message_id: int):
    from telebot.apihelper import ApiTelegramException
    try:
        rows = fetch_recent_transactions(user_id)
        text, markup = build_history_view(rows)
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    except ApiTelegramException:
        # Если сообщение устарело, отправляем новое
        rows = fetch_recent_transactions(user_id)
        text, markup = build_history_view(rows)
        bot.send_message(chat_id, text, reply_markup=markup)