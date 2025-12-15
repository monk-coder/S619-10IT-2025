"""Обработка транзакций"""
from telebot import types
from database import get_db, DB_LOCK
from utils.helpers import now_ts, parse_amount, CATEGORY_INFO
from utils.keyboards import build_categories_keyboard, build_comment_keyboard
from handlers.main_menu import ensure_user, set_step, get_step, pop_step, send_with_main_menu


def insert_transaction(user_id: int, tx_type: str, category: str, amount: float, comment: str) -> int:
    with DB_LOCK:
        db = get_db()
        cur = db.execute(
            "INSERT INTO transactions (user_id, type, category, amount, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, tx_type, category, amount, comment, now_ts()),
        )
        db.commit()
        return cur.lastrowid


def delete_transaction(user_id: int, tx_id: int) -> bool:
    with DB_LOCK:
        db = get_db()
        cur = db.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
        db.commit()
        return cur.rowcount > 0


def fetch_transactions(user_id: int, start_ts: float = None, end_ts: float = None, tx_type: str = None):
    query = ["SELECT * FROM transactions WHERE user_id = ?"]
    params = [user_id]
    
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
        db = get_db()
        return db.execute(" ".join(query), tuple(params)).fetchall()


def fetch_recent_transactions(user_id: int, limit: int = 10):
    with DB_LOCK:
        db = get_db()
        return db.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()


# Обработчики команд
def start_expense_flow(bot, message: types.Message):
    ensure_user(message)
    markup = build_categories_keyboard("add_expense")
    bot.send_message(
        message.chat.id,
        "<b>Добавление расхода</b>\n1. Выберите категорию\n2. Введите сумму\n3. Добавьте комментарий",
        reply_markup=markup,
    )


def start_income_flow(bot, message: types.Message):
    ensure_user(message)
    set_step(message.from_user.id, "income_amount", {})
    bot.send_message(
        message.chat.id,
        "<b>Добавление дохода</b>\nВведите сумму, затем укажите источник дохода.",
        reply_markup=build_main_menu_keyboard(),
    )


def handle_expense_amount(bot, message: types.Message, payload: dict) -> bool:
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


def handle_expense_comment(bot, message: types.Message, payload: dict) -> bool:
    comment = message.text.strip()
    finalize_expense_entry(bot, message.from_user.id, message.chat.id, payload, comment)
    return True


def finalize_expense_entry(bot, user_id: int, chat_id: int, payload: dict, comment: str):
    from telebot.apihelper import ApiTelegramException
    
    # Убираем клавиатуру комментария
    prompt_id = payload.get("comment_prompt_id")
    if prompt_id:
        try:
            bot.edit_message_reply_markup(chat_id, prompt_id)
        except ApiTelegramException:
            pass
            
    # Сохраняем транзакцию
    insert_transaction(
        user_id, 
        "expense", 
        payload.get("category"), 
        payload.get("amount", 0.0), 
        comment or None
    )
    
    pop_step(user_id)
    
    # Отправляем подтверждение
    emoji, title = CATEGORY_INFO.get(payload.get("category", "other"), ("✨", "Расход"))
    send_with_main_menu(
        bot,
        chat_id,
        f"Записано: {emoji} {title} — {payload.get('amount', 0.0):.2f}₽",
    )
    
    # Проверяем бюджет
    from handlers.budgets import check_budget_thresholds
    check_budget_thresholds(bot, user_id, payload.get("category", "other"), chat_id)


def handle_income_amount(bot, message: types.Message, payload: dict) -> bool:
    try:
        amount = parse_amount(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "Сумма должна быть положительным числом. Попробуйте снова:")
        return True
        
    payload["amount"] = amount
    set_step(message.from_user.id, "income_source", payload)
    bot.send_message(message.chat.id, "Укажите источник дохода (например, стипендия):")
    return True


def handle_income_source(bot, message: types.Message, payload: dict) -> bool:
    source = message.text.strip() or "Доход"
    insert_transaction(message.from_user.id, "income", source, payload.get("amount", 0.0), None)
    pop_step(message.from_user.id)
    send_with_main_menu(
        bot,
        message.chat.id,
        f"Доход {source} на сумму {payload.get('amount', 0.0):.2f}₽ добавлен.",
    )
    return True