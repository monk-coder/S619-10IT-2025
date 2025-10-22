import random
import telebot
from telebot.types import ReplyKeyboardMarkup

BOT_TOKEN = "8277822996:AAHdjF8a3zofwNAyBIeychcI7ZYjmcqik5I"
bot = telebot.TeleBot(BOT_TOKEN)
STARTING_BALANCE = 1000
users_db = {}

# 🔐 СПЕЦИАЛЬНЫЕ ПОЛЬЗОВАТЕЛИ
ADMIN_ID = 1528154226  # Админ
BANNED_USERS = [5631945112]  # Забаненные пользователи


def is_admin(user_id):
    """Проверяет, является ли пользователь админом"""
    return user_id == ADMIN_ID


def is_banned(user_id):
    """Проверяет, забанен ли пользователь"""
    return user_id in BANNED_USERS


def get_banned_message():
    """Сообщение для забаненных пользователей"""
    return "🚫 Вы забанены в этом казино! Доступ к играм запрещен."


def get_admin_message():
    """Приветствие для админа"""
    return "👑 Добро пожаловать, АДМИНИСТРАТОР!"


def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': STARTING_BALANCE,
            'games_played': 0,
            'wins': 0
        }
    return users_db[user_id]


def update_balance(user_id, amount):
    user = get_user(user_id)
    user['balance'] += amount
    user['games_played'] += 1
    if amount > 0:
        user['wins'] += 1
    return user['balance']


def create_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('🎰 Слоты', '🎯 Рулетка')
    keyboard.row('🎲 Кости', '💰 Баланс', '🆔 Мой ID')
    return keyboard


def create_admin_keyboard():
    """Клавиатура для админа с дополнительными функциями"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('🎰 Слоты', '🎯 Рулетка')
    keyboard.row('🎲 Кости', '💰 Баланс')
    keyboard.row('📊 Статистика', '👥 Пользователи')
    keyboard.row('🆔 Мой ID')
    return keyboard


# 🔍 КОМАНДА ДЛЯ ПОЛУЧЕНИЯ ID
@bot.message_handler(commands=['id', 'myid'])
def get_id_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or "не установлен"

    # Особое сообщение для админа
    if is_admin(user_id):
        role = "👑 АДМИНИСТРАТОР"
    elif is_banned(user_id):
        role = "🚫 ЗАБАНЕН"
    else:
        role = "👤 ПОЛЬЗОВАТЕЛЬ"

    bot.send_message(
        message.chat.id,
        f"📋 Ваша информация:\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"👤 Имя: {first_name}\n"
        f"📛 Username: @{username}\n"
        f"🎭 Роль: {role}\n"
        f"💬 Chat ID: `{message.chat.id}`",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)

    # 🔒 ПРОВЕРКА НА БАН
    if is_banned(user_id):
        bot.send_message(
            message.chat.id,
            f"😠 {get_banned_message()}\n\n"
            f"💳 Ваш баланс: {user_data['balance']} монет\n"
            f"❌ Игры недоступны",
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add('🆔 Мой ID')
        )
        return

    # 👑 ПРИВЕТСТВИЕ ДЛЯ АДМИНА
    if is_admin(user_id):
        bot.send_message(
            message.chat.id,
            f"{get_admin_message()}\n\n"
            f"💰 Баланс: {user_data['balance']} монет\n"
            f"🎮 Управляйте казином через меню ниже:",
            reply_markup=create_admin_keyboard()
        )
        return

    # 👤 ОБЫЧНОЕ ПРИВЕТСТВИЕ
    bot.send_message(
        message.chat.id,
        f"🎉 Добро пожаловать в Казино, {message.from_user.first_name}!\n"
        f"💰 Стартовый баланс: {user_data['balance']} монет\n\n"
        "Выберите игру:",
        reply_markup=create_keyboard()
    )


# 📊 СТАТИСТИКА ДЛЯ АДМИНА
@bot.message_handler(func=lambda message: message.text == '📊 Статистика')
def admin_stats(message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        bot.send_message(message.chat.id, "❌ Эта команда только для администратора!")
        return

    total_users = len(users_db)
    total_games = sum(user['games_played'] for user in users_db.values())
    total_wins = sum(user['wins'] for user in users_db.values())

    bot.send_message(
        message.chat.id,
        f"📊 СТАТИСТИКА КАЗИНО:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🎮 Всего игр сыграно: {total_games}\n"
        f"🏆 Всего побед: {total_wins}\n"
        f"🚫 Забанено: {len(BANNED_USERS)} пользователей"
    )


# 👥 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЯХ ДЛЯ АДМИНА
@bot.message_handler(func=lambda message: message.text == '👥 Пользователи')
def admin_users(message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        bot.send_message(message.chat.id, "❌ Эта команда только для администратора!")
        return

    bot.send_message(
        message.chat.id,
        f"👥 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЯХ:\n\n"
        f"👑 Админ: {ADMIN_ID}\n"
        f"🚫 Забаненные: {BANNED_USERS}\n"
        f"👤 Всего в базе: {len(users_db)} пользователей"
    )


# Кнопка "Мой ID"
@bot.message_handler(func=lambda message: message.text == '🆔 Мой ID')
def my_id_button(message):
    get_id_command(message)


# 🎰 ИГРЫ С ПРОВЕРКОЙ ДОСТУПА
def check_access(user_id):
    """Проверяет доступ пользователя к играм"""
    if is_banned(user_id):
        return False, get_banned_message()
    return True, None


@bot.message_handler(func=lambda message: message.text == '🎰 Слоты')
def slots_game(message):
    user_id = message.from_user.id

    # 🔒 ПРОВЕРКА ДОСТУПА
    access, error_message = check_access(user_id)
    if not access:
        bot.send_message(message.chat.id, error_message)
        return

    user_data = get_user(user_id)

    if user_data['balance'] < 10:
        bot.send_message(message.chat.id, "❌ Недостаточно монет! Нужно 10 монет")
        return

    symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
    result = [random.choice(symbols) for _ in range(3)]

    bet = 10
    payout = 0

    if result[0] == result[1] == result[2]:
        if result[0] == '7️⃣':
            payout = bet * 50
        elif result[0] == '💎':
            payout = bet * 20
        else:
            payout = bet * 5
    elif result[0] == result[1] or result[1] == result[2]:
        payout = bet * 2

    new_balance = update_balance(user_id, payout - bet)

    message_text = f"🎰 СЛОТ-МАШИНА 🎰\n\nРезультат: {' | '.join(result)}\n\n"
    if payout > 0:
        message_text += f"🎉 ВЫИГРЫШ! +{payout} монет!\n"
        if payout >= 100:
            message_text += "🔥 ДЖЕКПОТ! 🔥\n"
    else:
        message_text += "😢 Проигрыш\n"
    message_text += f"💰 Баланс: {new_balance} монет"

    bot.send_message(message.chat.id, message_text)


@bot.message_handler(func=lambda message: message.text == '🎲 Кости')
def dice_game(message):
    user_id = message.from_user.id

    # 🔒 ПРОВЕРКА ДОСТУПА
    access, error_message = check_access(user_id)
    if not access:
        bot.send_message(message.chat.id, error_message)
        return

    user_data = get_user(user_id)

    if user_data['balance'] < 15:
        bot.send_message(message.chat.id, "❌ Недостаточно монет! Нужно 15 монет")
        return

    bet = 15
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2

    payout = 0

    if total == 7:
        payout = bet * 3
        message_text = "🎉 Счастливая 7! x3"
    elif total >= 10:
        payout = bet * 2
        message_text = "👍 Больше 9! x2"
    elif total <= 4:
        payout = bet * 2
        message_text = "👎 Меньше 5! x2"
    else:
        message_text = "😐 Стандартный бросок"

    new_balance = update_balance(user_id, payout - bet)

    bot.send_message(
        message.chat.id,
        f"🎲 КОСТИ 🎲\n\n"
        f"Бросок: {dice1} + {dice2} = {total}\n"
        f"{message_text}\n\n"
        f"💰 Баланс: {new_balance} монет"
    )


@bot.message_handler(func=lambda message: message.text == '🎯 Рулетка')
def roulette_game(message):
    user_id = message.from_user.id

    # 🔒 ПРОВЕРКА ДОСТУПА
    access, error_message = check_access(user_id)
    if not access:
        bot.send_message(message.chat.id, error_message)
        return

    user_data = get_user(user_id)

    if user_data['balance'] < 20:
        bot.send_message(message.chat.id, "❌ Недостаточно монет! Нужно 20 монет")
        return

    number = random.randint(0, 36)

    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

    bet = 20
    payout = 0

    if number == 0:
        message_text = "🟢 0 - ЗЕЛЕНЫЙ! ДЖЕКПОТ! x35"
        payout = bet * 35
    elif number in red_numbers:
        message_text = f"🔴 {number} - КРАСНЫЙ! Выигрыш x2"
        payout = bet * 2
    elif number in black_numbers:
        message_text = f"⚫ {number} - ЧЕРНЫЙ! Выигрыш x2"
        payout = bet * 2
    else:
        message_text = f"❌ {number} - Проигрыш"
        payout = 0

    new_balance = update_balance(user_id, payout - bet)

    roulette_wheel = "🎯🎰🎯🎰🎯🎰🎯"

    bot.send_message(
        message.chat.id,
        f"{roulette_wheel} РУЛЕТКА {roulette_wheel}\n\n"
        f"🎡 Выпало число: {number}\n"
        f"📢 Результат: {message_text}\n\n"
        f"💵 Ставка: {bet} монет\n"
        f"💰 Выигрыш: {payout} монет\n"
        f"💳 Баланс: {new_balance} монет\n\n"
        f"🎮 Удачи в следующей игре!"
    )


@bot.message_handler(func=lambda message: message.text == '💰 Баланс')
def balance_command(message):
    user_data = get_user(message.from_user.id)

    # Особое сообщение для забаненных
    if is_banned(message.from_user.id):
        status = "🚫 ЗАБАНЕН"
    elif is_admin(message.from_user.id):
        status = "👑 АДМИНИСТРАТОР"
    else:
        status = "👤 ИГРОК"

    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {user_data['balance']} монет\n"
        f"🎮 Игр сыграно: {user_data['games_played']}\n"
        f"🏆 Побед: {user_data['wins']}\n"
        f"🎭 Статус: {status}"
    )


if __name__ == "__main__":
    print("🎰 Казино-бот запущен!")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"🚫 Забаненные: {BANNED_USERS}")
    bot.infinity_polling()