from datetime import datetime
from telebot import types
from database import db_session
from helpers import month_range, category_info

def set_budget(user_id, category, amount):
    with db_session() as db:
        db.execute("""
            INSERT INTO budgets (user_id, category, amount) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET amount = excluded.amount
        """, (user_id, category, amount))

def get_budgets(user_id):
    with db_session() as db:
        return db.execute("SELECT category, amount FROM budgets WHERE user_id = ?", (user_id,)).fetchall()

def get_spent(user_id, category, start, end):
    with db_session() as db:
        row = db.execute("""
            SELECT SUM(amount) as spent FROM transactions 
            WHERE user_id = ? AND category = ? AND created_at BETWEEN ? AND ? AND type = 'expense'
        """, (user_id, category, start.timestamp(), end.timestamp())).fetchone()
        return row['spent'] or 0

def show_goals(bot, message):
    budgets = get_budgets(message.from_user.id)
    if not budgets:
        bot.send_message(message.chat.id, "Бюджеты не заданы. Используйте /set_budget.")
        return
    
    start, end = month_range()
    lines = ["<b>Прогресс по бюджетам</b>"]
    
    for row in budgets:
        spent = get_spent(message.from_user.id, row['category'], start, end)
        percent = (spent / row['amount'] * 100) if row['amount'] else 0
        emoji, name = category_info(row['category'])
        bar = "█" * min(int(percent/5), 20)
        lines.append(f"{emoji} {name}: {spent:.2f}/{row['amount']:.2f}₽ {bar} {percent:.0f}%")
    
    bot.send_message(message.chat.id, "\n".join(lines), parse_mode='HTML')