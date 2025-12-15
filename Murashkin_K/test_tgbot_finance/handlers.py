import telebot
import csv
import os
from telebot import types
from datetime import datetime, timedelta
from keyboards import categories_keyboard
from utils import text_graph
from data_manager import save_transaction, save_budget, load_data, save_data
from config import CATEGORIES

data = load_data()
user_sessions = {}

def register_handlers(bot: telebot.TeleBot):
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id,
                         "Привет! Это тестовая версия бота.\n"
                         "Команды:\n"
                         "/add - добавить расход\n"
                         "/income - добавить доход\n"
                         "/today, /week, /month - статистика расходов\n"
                         "/history - последние 10 операций\n"
                         "/set_budget <категория> <сумма> - установить бюджет\n"
                         "/goals - прогресс по бюджетам\n"
                         "/export <ГГГГ-ММ> - экспорт CSV")

    @bot.message_handler(commands=['help'])
    def help_message(message):
        help_text = (
            "Справка по боту:\n\n"
            "/add — добавить расход (быстро «в два тапа»)\n"
            "/income — добавить доход (с указанием суммы и источника)\n"
            "/today — статистика расходов за сегодня\n"
            "/week — статистика расходов за последние 7 дней\n"
            "/month — статистика расходов за текущий месяц\n"
            "/history — последние 10 операций с возможностью удаления\n"
            "/set_budget <категория> <сумма> — установить лимит бюджета по категории\n"
            "/goals — просмотр прогресса по бюджетам\n"
            "/export <ГГГГ-ММ> — экспорт транзакций за месяц в CSV\n"
            "/help — показать это сообщение"
        )
        bot.send_message(message.chat.id, help_text)

    @bot.message_handler(commands=['add'])
    def add_expense_start(message):
        user_id = str(message.from_user.id)
        user_sessions[user_id] = {'type': 'expense'}
        bot.send_message(message.chat.id, "Выберите категорию расхода:", reply_markup=categories_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data in CATEGORIES)
    def choose_category(call):
        user_id = str(call.from_user.id)
        if user_id not in user_sessions:
            bot.answer_callback_query(call.id, "Пожалуйста, сначала используйте /add или /income")
            return
        user_sessions[user_id]['category'] = call.data
        bot.answer_callback_query(call.id, f"Категория '{CATEGORIES[call.data]}' выбрана. Введите сумму числом:")
        msg = bot.send_message(call.message.chat.id, "Введите сумму (например, 500):")
        bot.register_next_step_handler(msg, process_amount)

    def process_amount(message):
        user_id = str(message.from_user.id)
        if user_id not in user_sessions:
            bot.send_message(message.chat.id, "Сессия окончена. Начните заново с /add или /income.")
            return
        try:
            amount = float(message.text.replace(',', '.'))
            if amount <= 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "Неверный ввод. Введите положительное число суммы:")
            bot.register_next_step_handler(msg, process_amount)
            return
        user_sessions[user_id]['amount'] = amount
        msg = bot.send_message(message.chat.id, "Введите комментарий или напишите 'пропустить':")
        bot.register_next_step_handler(msg, process_comment)

    def process_comment(message):
        user_id = str(message.from_user.id)
        comment = message.text.strip()
        if comment.lower() == 'пропустить':
            comment = ''
        session = user_sessions.pop(user_id)
        tr = {
            'user_id': user_id,
            'type': session.get('type', 'expense'),
            'category': session.get('category', 'other'),
            'amount': session['amount'],
            'comment': comment,
            'datetime': datetime.now().isoformat()
        }
        save_transaction(data, tr)
        check_budget(user_id, tr['category'])
        bot.send_message(message.chat.id,
                         f"Транзакция сохранена:\n"
                         f"{CATEGORIES.get(tr['category'], 'Другое')}, {tr['amount']}₽\n"
                         f"Комментарий: {tr['comment']}\n"
                         f"Дата: {tr['datetime']}")

    @bot.message_handler(commands=['income'])
    def income_start(message):
        user_id = str(message.from_user.id)
        user_sessions[user_id] = {'type': 'income'}
        bot.send_message(message.chat.id, "Введите сумму и источник дохода через пробел, например:\n500 Подработка")
        bot.register_next_step_handler_by_chat_id(message.chat.id, process_income)

    def process_income(message):
        user_id = str(message.from_user.id)
        try:
            parts = message.text.split(maxsplit=1)
            amount = float(parts[0].replace(',', '.'))
            if amount <= 0:
                raise ValueError
            source = parts[1] if len(parts) > 1 else ''
        except Exception:
            msg = bot.send_message(message.chat.id, "Ошибка! Используйте формат: сумма источник")
            bot.register_next_step_handler(msg, process_income)
            return
        tr = {
            'user_id': user_id,
            'type': 'income',
            'category': source or "Доход",
            'amount': amount,
            'comment': '',
            'datetime': datetime.now().isoformat()
        }
        save_transaction(data, tr)
        bot.send_message(message.chat.id, f"Доход {amount}₽ от \"{source}\" добавлен.")

    @bot.message_handler(commands=['today', 'week', 'month'])
    def statistics(message):
        user_id = str(message.from_user.id)
        now = datetime.now()
        text_period = message.text[1:].lower()
        if text_period == 'today':
            start = datetime(now.year, now.month, now.day)
        elif text_period == 'week':
            start = now - timedelta(days=7)
        elif text_period == 'month':
            start = datetime(now.year, now.month, 1)
        else:
            bot.send_message(message.chat.id, "Команда не распознана.")
            return

        user_transactions = [t for t in data["transactions"] if t["user_id"] == user_id and t["type"] == 'expense' and datetime.fromisoformat(t['datetime']) >= start]
        if not user_transactions:
            bot.send_message(message.chat.id, f"Нет расходов за {text_period}.")
            return

        sums = {}
        for t in user_transactions:
            sums[t['category']] = sums.get(t['category'], 0) + t['amount']

        text = f"Статистика расходов за {text_period}:\n" + text_graph(sums)
        if text_period == 'month':
            days = (now - start).days + 1
            total = sum(sums.values())
            avg = total / days if days else 0
            text += f"\n\nОбщая сумма: {total}₽\nСредний расход в день: {avg:.2f}₽"
        bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=['history'])
    def history(message):
        user_id = str(message.from_user.id)
        user_transactions = [t for t in data["transactions"] if t["user_id"] == user_id]
        if not user_transactions:
            bot.send_message(message.chat.id, "История пуста.")
            return
        last10 = user_transactions[-10:]
        for idx, t in enumerate(reversed(last10)):
            dt = datetime.fromisoformat(t['datetime']).strftime('%Y-%m-%d %H:%M')
            cat_name = CATEGORIES.get(t['category'], t['category'])
            txt = f"{idx+1}. {dt} | {cat_name} | {t['amount']}₽"
            if t['comment']:
                txt += f" | {t['comment']}"
            markup = types.InlineKeyboardMarkup()
            global_index = data["transactions"].index(t)
            markup.add(types.InlineKeyboardButton("Удалить", callback_data=f"delete_{global_index}"))
            bot.send_message(message.chat.id, txt, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("delete_"))
    def delete_transaction(call):
        idx = int(call.data.split("_")[1])
        user_id = str(call.from_user.id)
        if 0 <= idx < len(data["transactions"]):
            tr = data["transactions"][idx]
            if tr["user_id"] == user_id:
                data["transactions"].pop(idx)
                save_data(data)
                bot.edit_message_text("Транзакция удалена", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id, "Удалено")
                return
        bot.answer_callback_query(call.id, "Ошибка удаления")

    @bot.message_handler(commands=['set_budget'])
    def set_budget(message):
        user_id = str(message.from_user.id)
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            bot.send_message(message.chat.id, "Используйте: /set_budget <категория> <сумма>\nнапример: /set_budget еда 5000")
            return
        cat_name = args[1].lower()
        limit = args[2]

        cat_key = None
        for key, name in CATEGORIES.items():
            name_without_emoji = ''.join(filter(str.isalpha, name.lower()))
            if cat_name in name_without_emoji:
                cat_key = key
                break

        if not cat_key:
            categories_list = "\n".join(CATEGORIES.values())
            bot.send_message(message.chat.id, f"Категория не найдена. Доступные категории:\n{categories_list}")
            return

        try:
            limit_val = float(limit)
            if limit_val <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "Сумма должна быть положительным числом.")
            return

        if user_id not in data["budgets"]:
            data["budgets"][user_id] = {}
        data["budgets"][user_id][cat_key] = limit_val
        save_data(data)

        bot.send_message(message.chat.id, f"Бюджет установлен: {CATEGORIES[cat_key]} - {limit_val}₽")

    @bot.message_handler(commands=['goals'])
    def show_goals(message):
        user_id = str(message.from_user.id)
        budgets_user = data["budgets"].get(user_id, {})
        if not budgets_user:
            bot.send_message(message.chat.id, "Бюджеты не установлены.")
            return
        now = datetime.now()
        start = datetime(now.year, now.month, 1)
        user_expenses = [t for t in data["transactions"] if t["user_id"] == user_id and t["type"] == 'expense' and datetime.fromisoformat(t["datetime"]) >= start]
        sums = {}
        for t in user_expenses:
            sums[t["category"]] = sums.get(t["category"], 0) + t["amount"]
        lines = ["Прогресс по бюджетам:"]
        for cat, limit in budgets_user.items():
            spent = sums.get(cat, 0)
            perc = spent / limit * 100 if limit else 0
            lines.append(f"{CATEGORIES.get(cat, 'Другое')}: {spent:.2f} из {limit}₽ ({perc:.1f}%)")
        bot.send_message(message.chat.id, "\n".join(lines))

    def check_budget(user_id, category):
        budgets_user = data["budgets"].get(user_id, {})
        if category not in budgets_user:
            return
        now = datetime.now()
        start = datetime(now.year, now.month, 1)
        user_expenses = [t for t in data["transactions"] if t["user_id"] == user_id and t["type"] == 'expense' and t['category'] == category and datetime.fromisoformat(t["datetime"]) >= start]
        spent = sum(t["amount"] for t in user_expenses)
        limit = budgets_user[category]
        if spent >= limit and spent - limit < 1:
            bot.send_message(user_id, f"⚠️ Вы достигли 100% бюджета по категории {CATEGORIES[category]}!")
        elif spent >= 0.8 * limit and spent - 0.8 * limit < 1:
            bot.send_message(user_id, f"⚠️ Вы достигли 80% бюджета по категории {CATEGORIES[category]}!")

    @bot.message_handler(commands=['export'])
    def export_csv(message):
        user_id = str(message.from_user.id)
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.send_message(message.chat.id, "Используйте: /export ГГГГ-ММ, например:\n/export 2025-11")
            return
        month = args[1]
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            bot.send_message(message.chat.id, "Неправильный формат даты. Используйте ГГГГ-ММ")
            return
        user_transactions = [t for t in data["transactions"] if t["user_id"] == user_id and t["datetime"].startswith(month)]
        if not user_transactions:
            bot.send_message(message.chat.id, "Данные за этот месяц отсутствуют.")
            return
        filename = f"export_{user_id}_{month}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Дата и время", "Тип", "Категория", "Сумма", "Комментарий"])
            for t in user_transactions:
                writer.writerow([t["datetime"], t["type"], CATEGORIES.get(t["category"], t["category"]), t["amount"], t["comment"]])
        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f)
        os.remove(filename)

