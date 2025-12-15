from telebot import types
from database import db_session
from helpers import parse_amount, category_info
import keyboards as kb

def add_transaction(user_id, tx_type, category, amount, comment=None):
    from datetime import datetime
    with db_session() as db:
        cursor = db.execute("""
            INSERT INTO transactions (user_id, type, category, amount, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, tx_type, category, amount, comment, datetime.now().timestamp()))
        return cursor.lastrowid

def delete_transaction(user_id, tx_id):
    with db_session() as db:
        cursor = db.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
        return cursor.rowcount > 0

def get_recent(user_id, limit=10):
    with db_session() as db:
        return db.execute("""
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit)).fetchall()

def start_expense(bot, message):
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=kb.categories_menu())

def start_income(bot, message):
    bot.send_message(message.chat.id, "Введите сумму дохода:")

def process_expense(user_id, chat_id, category, amount, comment=None):
    tx_id = add_transaction(user_id, 'expense', category, amount, comment)
    emoji, name = category_info(category)
    return f"✅ {emoji} {name}: {amount:.2f}₽ (id: {tx_id})"

def process_income(user_id, chat_id, amount, source):
    tx_id = add_transaction(user_id, 'income', source, amount, None)
    return f"✅ Доход: {source} {amount:.2f}₽ (id: {tx_id})"