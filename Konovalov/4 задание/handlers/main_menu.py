from datetime import datetime
from database import db_session
import keyboards as kb

user_states = {}

def save_user(user_id, username, first_name, last_name):
    with db_session() as db:
        db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, created_at) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, datetime.now().timestamp()))

def set_state(user_id, state, data=None):
    user_states[user_id] = {"state": state, "data": data or {}}

def get_state(user_id):
    return user_states.get(user_id)

def pop_state(user_id):
    return user_states.pop(user_id, None)

def send_menu(bot, chat_id, text, parse_mode='HTML'):
    bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=kb.main_menu())