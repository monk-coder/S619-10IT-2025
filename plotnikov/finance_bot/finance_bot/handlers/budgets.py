"""Управление бюджетами"""
from datetime import datetime
from database import get_db, DB_LOCK
from utils.helpers import month_bounds, now_ts, resolve_category, CATEGORY_INFO, aggregate_by_category
from handlers.transactions import fetch_transactions, fetch_recent_transactions
from handlers.main_menu import send_with_main_menu


def upsert_budget(user_id: int, category: str, amount: float) -> None:
    with DB_LOCK:
        db = get_db()
        db.execute(
            "INSERT INTO budgets (user_id, category, amount) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, category) DO UPDATE SET amount = excluded.amount",
            (user_id, category, amount),
        )
        db.commit()


def fetch_budgets(user_id: int):
    with DB_LOCK:
        db = get_db()
        return db.execute("SELECT category, amount FROM budgets WHERE user_id = ?", (user_id,)).fetchall()


def get_budget(user_id: int, category: str) -> float:
    with DB_LOCK:
        db = get_db()
        row = db.execute("SELECT amount FROM budgets WHERE user_id = ? AND category = ?", (user_id, category)).fetchone()
    return row["amount"] if row else None


def budget_alert_sent(user_id: int, category: str, period: str, threshold: str) -> bool:
    with DB_LOCK:
        db = get_db()
        row = db.execute(
            "SELECT 1 FROM budget_alerts WHERE user_id = ? AND category = ? AND period = ? AND threshold = ?",
            (user_id, category, period, threshold),
        ).fetchone()
    return bool(row)


def mark_budget_alert(user_id: int, category: str, period: str, threshold: str) -> None:
    with DB_LOCK:
        db = get_db()
        db.execute(
            "INSERT OR IGNORE INTO budget_alerts (user_id, category, period, threshold, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, period, threshold, now_ts()),
        )
        db.commit()


def check_budget_thresholds(bot, user_id: int, category: str, chat_id: int) -> None:
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


def show_goals(bot, message: types.Message):
    from handlers.main_menu import ensure_user
    ensure_user(message)
    
    budgets = fetch_budgets(message.from_user.id)
    if not budgets:
        send_with_main_menu(bot, message.chat.id, "Бюджеты не заданы. Используйте /set_budget.")
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
        
    send_with_main_menu(bot, message.chat.id, "\n".join(lines))