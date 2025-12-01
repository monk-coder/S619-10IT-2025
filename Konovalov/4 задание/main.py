import telebot
from telebot import types
import logging
from datetime import datetime, timedelta

from config import BOT_TOKEN, CATEGORIES
from database import db_session
import keyboards as kb

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

# Состояния пользователей
user_state = {}

def set_state(user_id, state, data=None):
    user_state[user_id] = {"state": state, "data": data or {}}

def get_state(user_id):
    return user_state.get(user_id, {})

# Основные команды
@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    user = message.from_user
    with db_session() as db:
        db.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, created_at) VALUES (?,?,?,?,?)",
                  (user.id, user.username, user.first_name, user.last_name, datetime.now().timestamp()))
    
    bot.send_message(message.chat.id,
        "💰 <b>Финансовый помощник</b>\n"
        "Записывайте расходы и доходы, следите за бюджетом.\n"
        "Используйте кнопки ниже:",
        parse_mode='HTML',
        reply_markup=kb.main_menu())

@bot.message_handler(commands=['add'])
def add_expense_cmd(message):
    set_state(message.from_user.id, "category")
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=kb.categories_menu())

# Кнопки категорий
@bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
def category_selected(call):
    user_id = call.from_user.id
    category = call.data.replace('cat_', '')
    
    set_state(user_id, "amount", {"category": category})
    emoji, name = CATEGORIES.get(category, ("📦", category))
    
    bot.answer_callback_query(call.id, f"{emoji} {name}")
    bot.send_message(call.message.chat.id, f"Введите сумму для {emoji} {name}:")

# Обработка текста
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    
    if state.get("state") == "amount":
        try:
            amount = float(message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError
            
            set_state(user_id, "comment", {
                "category": state["data"]["category"],
                "amount": amount
            })
            
            bot.send_message(message.chat.id,
                f"Сумма: {amount:.2f}₽\n"
                "Введите комментарий или нажмите /skip:",
                reply_markup=types.ReplyKeyboardRemove())
                
        except ValueError:
            bot.send_message(message.chat.id, "❌ Введите корректную сумму (например: 150.50)")
    
    elif state.get("state") == "comment":
        category = state["data"]["category"]
        amount = state["data"]["amount"]
        comment = message.text if message.text != "/skip" else None
        
        with db_session() as db:
            db.execute(
                "INSERT INTO transactions (user_id, type, category, amount, comment, created_at) VALUES (?,?,?,?,?,?)",
                (user_id, 'expense', category, amount, comment, datetime.now().timestamp())
            )
        
        emoji, name = CATEGORIES.get(category, ("📦", category))
        bot.send_message(message.chat.id,
            f"✅ <b>Запись добавлена</b>\n"
            f"{emoji} {name}: {amount:.2f}₽\n"
            f"Комментарий: {comment or 'нет'}",
            parse_mode='HTML',
            reply_markup=kb.main_menu())
        
        set_state(user_id, None)
    
    elif message.text == "➕ Расход":
        add_expense_cmd(message)
    
    elif message.text == "📊 Сегодня":
        show_stats(message, "today")
    
    elif message.text == "📈 Неделя":
        show_stats(message, "week")
    
    elif message.text == "📰 История":
        show_history(message)
    
    else:
        bot.send_message(message.chat.id, "Используйте кнопки меню или /help")

# Статистика
def show_stats(message, period):
    user_id = message.from_user.id
    now = datetime.now()
    
    if period == "today":
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
    elif period == "week":
        start = now - timedelta(days=7)
        end = now
    
    with db_session() as db:
        result = db.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND created_at BETWEEN ? AND ?
            GROUP BY category
        """, (user_id, start.timestamp(), end.timestamp())).fetchall()
    
    if not result:
        bot.send_message(message.chat.id, "Нет данных за этот период", reply_markup=kb.main_menu())
        return
    
    text = f"📊 <b>Расходы за {period}:</b>\n"
    total = 0
    
    for row in result:
        emoji, name = CATEGORIES.get(row['category'], ("📦", row['category']))
        text += f"{emoji} {name}: {row['total']:.2f}₽\n"
        total += row['total']
    
    text += f"\n<b>Итого: {total:.2f}₽</b>"
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=kb.main_menu())

# История
def show_history(message):
    user_id = message.from_user.id
    
    with db_session() as db:
        transactions = db.execute("""
            SELECT id, category, amount, comment, created_at
            FROM transactions 
            WHERE user_id = ? AND type = 'expense'
            ORDER BY created_at DESC 
            LIMIT 10
        """, (user_id,)).fetchall()
    
    if not transactions:
        bot.send_message(message.chat.id, "История пуста", reply_markup=kb.main_menu())
        return
    
    text = "📜 <b>Последние 10 операций:</b>\n\n"
    for tx in transactions:
        date = datetime.fromtimestamp(tx['created_at']).strftime('%d.%m %H:%M')
        emoji, name = CATEGORIES.get(tx['category'], ("📦", tx['category']))
        text += f"{date} | {emoji} {name}: {tx['amount']:.2f}₽\n"
        if tx['comment']:
            text += f"   📝 {tx['comment'][:30]}\n"
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=kb.main_menu())

# Запуск
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()