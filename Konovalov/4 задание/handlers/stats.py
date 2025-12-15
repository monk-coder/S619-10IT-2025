from datetime import datetime
from helpers import today, week, month, category_info
from database import db_session

def get_stats(user_id, period_name, start, end):
    with db_session() as db:
        rows = db.execute("""
            SELECT category, SUM(amount) as total 
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND created_at BETWEEN ? AND ?
            GROUP BY category
        """, (user_id, start.timestamp(), end.timestamp())).fetchall()
    
    if not rows:
        return f"Нет расходов за {period_name}."
    
    total = sum(r['total'] for r in rows)
    lines = [f"<b>Расходы за {period_name}</b>"]
    
    for row in rows:
        percent = (row['total'] / total * 100) if total else 0
        emoji, name = category_info(row['category'])
        bar = "█" * min(int(percent/5), 20)
        lines.append(f"{emoji} {name}: {row['total']:.2f}₽ {bar} {percent:.0f}%")
    
    lines.append(f"\n<b>Итого: {total:.2f}₽</b>")
    return "\n".join(lines)

def show_today(bot, message):
    start, end = today()
    bot.send_message(message.chat.id, get_stats(message.from_user.id, "сегодня", start, end), parse_mode='HTML')

def show_week(bot, message):
    start, end = week()
    bot.send_message(message.chat.id, get_stats(message.from_user.id, "неделю", start, end), parse_mode='HTML')

def show_month(bot, message):
    start, end = month()
    bot.send_message(message.chat.id, get_stats(message.from_user.id, "месяц", start, end), parse_mode='HTML')