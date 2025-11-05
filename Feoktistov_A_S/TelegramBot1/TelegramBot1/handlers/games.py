import random
import telebot
from telebot import apihelper
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import time
import datetime

# ⚠️ ОТКЛЮЧАЕМ ПРОВЕРКУ SSL
apihelper.SSL_CONTEXT = None

BOT_TOKEN = "8277822996:AAHdjF8a3zofwNAyBIeychcI7ZYjmcqik5I"
bot = telebot.TeleBot(BOT_TOKEN)
STARTING_BALANCE = 1000
users_db = {}

# 🔐 СПЕЦИАЛЬНЫЕ ПОЛЬЗОВАТЕЛИ
ADMIN_ID = 1528154226
BANNED_USER_IDS = [5479449387]
BANNED_USERNAMES = []

# 🎰 ДОСТУПНЫЕ СТАВКИ
AVAILABLE_BETS = {
    '🎰 Слоты': [10, 25, 50, 100],
    '🎲 Кости': [15, 30, 60, 120],
    '🎯 Рулетка': [20, 40, 80, 160]
}

# 💰 СИСТЕМА БОНУСОВ
BONUS_AMOUNT = 400
BONUS_COOLDOWN = 3 * 60 * 60

# Хранилища
user_bets = {}
last_bonus_time = {}


def is_admin(user_id):
    return user_id == ADMIN_ID


def is_banned(user_id, username=None):
    if user_id in BANNED_USER_IDS:
        return True
    if username and username.lower() in [u.lower() for u in BANNED_USERNAMES]:
        return True
    return False


def check_access(user_id, username=None):
    if is_banned(user_id, username):
        return False, "🚫 Вы забанены в этом казино! Доступ к играм запрещен."
    return True, None


def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': STARTING_BALANCE,
            'games_played': 0,
            'wins': 0,
            'recent_wins': 0,
            'bonuses_received': 0
        }
    return users_db[user_id]


def update_balance(user_id, amount):
    user = get_user(user_id)
    user['balance'] += amount
    user['games_played'] += 1
    if amount > 0:
        user['wins'] += 1
    users_db[user_id] = user
    return user['balance']


def can_get_bonus(user_id):
    current_time = time.time()

    if user_id not in last_bonus_time:
        return True, 0

    last_time = last_bonus_time[user_id]
    time_passed = current_time - last_time
    time_remaining = BONUS_COOLDOWN - time_passed

    if time_passed >= BONUS_COOLDOWN:
        return True, 0
    else:
        return False, time_remaining


def give_bonus(user_id):
    if user_id not in last_bonus_time:
        last_bonus_time[user_id] = 0

    can_receive, time_left = can_get_bonus(user_id)

    if can_receive:
        user = get_user(user_id)
        user['balance'] += BONUS_AMOUNT
        user['bonuses_received'] += 1
        users_db[user_id] = user
        last_bonus_time[user_id] = time.time()
        return True, BONUS_AMOUNT
    else:
        return False, time_left


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}ч {minutes}м"


def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('🎰 Слоты', '🎯 Рулетка')
    keyboard.row('🎲 Кости', '💰 Баланс', '🎁 Бонус')
    keyboard.row('🆔 Мой ID')
    return keyboard


def create_bet_keyboard(game_type):
    keyboard = InlineKeyboardMarkup()
    bets = AVAILABLE_BETS[game_type]

    row1 = []
    row2 = []
    for i, bet in enumerate(bets):
        if i < 2:
            row1.append(InlineKeyboardButton(f"{bet} 🪙", callback_data=f"bet_{game_type}_{bet}"))
        else:
            row2.append(InlineKeyboardButton(f"{bet} 🪙", callback_data=f"bet_{game_type}_{bet}"))

    if row1:
        keyboard.row(*row1)
    if row2:
        keyboard.row(*row2)

    keyboard.row(InlineKeyboardButton("❌ Отмена", callback_data="cancel_bet"))

    return keyboard


# 🔍 КОМАНДА ДЛЯ ПОЛУЧЕНИЯ ID
@bot.message_handler(commands=['id', 'myid'])
def get_id_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or "не установлен"

    if is_admin(user_id):
        role = "👑 АДМИНИСТРАТОР"
    elif is_banned(user_id, username):
        role = "🚫 ЗАБАНЕН"
    else:
        role = "👤 ПОЛЬЗОВАТЕЛЬ"

    bot.send_message(
        message.chat.id,
        f"📋 Ваша информация:\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"👤 Имя: {first_name}\n"
        f"📛 Username: @{username}\n"
        f"🎭 Роль: {role}",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_data = get_user(user_id)

    if is_banned(user_id, username):
        bot.send_message(
            message.chat.id,
            f"😠 Вы забанены в этом казино!\n\n"
            f"💳 Ваш баланс: {user_data['balance']} монет\n"
            f"❌ Игры недоступны"
        )
        return

    welcome_text = f"🎉 Добро пожаловать в Казино, {message.from_user.first_name}!\n"
    welcome_text += f"💰 Стартовый баланс: {user_data['balance']} монет\n\n"
    welcome_text += "🎰 Теперь вы можете выбирать размер ставки в играх!\n"
    welcome_text += f"🎁 Каждые 3 часа получайте бонус +{BONUS_AMOUNT} монет!\n\n"
    welcome_text += "Выберите игру:"

    if is_admin(user_id):
        welcome_text = f"👑 Добро пожаловать, АДМИНИСТРАТОР!\n\n" + welcome_text

    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_keyboard())


@bot.message_handler(func=lambda message: message.text == '🆔 Мой ID')
def my_id_button(message):
    get_id_command(message)


@bot.message_handler(func=lambda message: message.text == '💰 Баланс')
def balance_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_data = get_user(user_id)

    if is_banned(user_id, username):
        status = "🚫 ЗАБАНЕН"
    elif is_admin(user_id):
        status = "👑 АДМИНИСТРАТОР"
    else:
        status = "👤 ИГРОК"

    can_receive, time_left = can_get_bonus(user_id)

    bonus_info = ""
    if can_receive:
        bonus_info = f"🎁 Бонус доступен: +{BONUS_AMOUNT} монет"
    else:
        bonus_info = f"⏰ Бонус через: {format_time(time_left)}"

    bot.send_message(
        message.chat.id,
        f"💰 БАЛАНС:\n\n"
        f"💳 Сумма: {user_data['balance']} монет\n"
        f"🎮 Игр сыграно: {user_data['games_played']}\n"
        f"🏆 Побед: {user_data['wins']}\n"
        f"🎁 Бонусов получено: {user_data.get('bonuses_received', 0)}\n"
        f"🎭 Статус: {status}\n\n"
        f"{bonus_info}"
    )


@bot.message_handler(func=lambda message: message.text == '🎁 Бонус')
def bonus_command(message):
    user_id = message.from_user.id
    username = message.from_user.username

    access, error_message = check_access(user_id, username)
    if not access:
        bot.send_message(message.chat.id, error_message)
        return

    # Анимация получения бонуса
    loading_msg = bot.send_message(message.chat.id, "🎁 Проверка бонуса...")
    time.sleep(1)

    success, result = give_bonus(user_id)

    if success:
        user_data = get_user(user_id)
        bot.edit_message_text(
            "💰 Бонус обнаружен! Загружаем...",
            message.chat.id,
            loading_msg.message_id
        )
        time.sleep(1)

        # Анимация падающих монет
        coin_frames = [
            "💸 *С НАМИ БОГ!* 💸",
            "💰 *ПОЛУЧАЕМ БОНУС* 💰",
            "🎊 *ПОЗДРАВЛЯЕМ!* 🎊"
        ]

        for frame in coin_frames:
            bot.edit_message_text(frame, message.chat.id, loading_msg.message_id)
            time.sleep(0.7)

        bot.edit_message_text(
            f"🎊 ПОЗДРАВЛЯЕМ! 🎊\n\n"
            f"💰 Вы получили бонус: +{BONUS_AMOUNT} монет!\n"
            f"💳 Теперь у вас: {user_data['balance']} монет\n"
            f"🎁 Всего бонусов получено: {user_data['bonuses_received']}\n\n"
            f"⏰ Следующий бонус через 3 часа\n"
            f"🎰 Удачи в играх!",
            message.chat.id,
            loading_msg.message_id
        )
    else:
        time_left = format_time(result)
        bot.edit_message_text(
            f"⏰ БОНУС ЕЩЕ НЕ ДОСТУПЕН\n\n"
            f"💤 Вы уже получали бонус недавно\n"
            f"⏳ Приходите через: {time_left}\n\n"
            f"🎁 Каждые 3 часа: +{BONUS_AMOUNT} монет",
            message.chat.id,
            loading_msg.message_id
        )


# 🎰 ИГРЫ С ВЫБОРОМ СТАВКИ
@bot.message_handler(func=lambda message: message.text == '🎰 Слоты')
def slots_bet(message):
    user_id = message.from_user.id
    username = message.from_user.username

    access, error_message = check_access(user_id, username)
    if not access:
        bot.send_message(message.chat.id, error_message)
        return

    user_data = get_user(user_id)

    min_bet = min(AVAILABLE_BETS['🎰 Слоты'])
    if user_data['balance'] < min_bet:
        bot.send_message(message.chat.id,
                         f"❌ Недостаточно монет! Минимальная ставка: {min_bet} монет\n💡 Используйте команду '🎁 Бонус' для пополнения баланса")
        return

    bot.send_message(
        message.chat.id,
        f"🎰 СЛОТ-МАШИНА\n\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"💵 Выберите размер ставки:",
        reply_markup=create_bet_keyboard('🎰 Слоты')
    )


@bot.message_handler(func=lambda message: message.text == '🎲 Кости')
def dice_bet(message):
    user_id = message.from_user.id
    username = message.from_user.username

    access, error_message = check_access(user_id, username)
    if not access:
        bot.send_message(message.chat.id, error_message)
        return

    user_data = get_user(user_id)

    min_bet = min(AVAILABLE_BETS['🎲 Кости'])
    if user_data['balance'] < min_bet:
        bot.send_message(message.chat.id,
                         f"❌ Недостаточно монет! Минимальная ставка: {min_bet} монет\n💡 Используйте команду '🎁 Бонус' для пополнения баланса")
        return

    bot.send_message(
        message.chat.id,
        f"🎲 КОСТИ\n\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"💵 Выберите размер ставки:",
        reply_markup=create_bet_keyboard('🎲 Кости')
    )


@bot.message_handler(func=lambda message: message.text == '🎯 Рулетка')
def roulette_bet(message):
    user_id = message.from_user.id
    username = message.from_user.username

    access, error_message = check_access(user_id, username)
    if not access:
        bot.send_message(message.chat.id, error_message)
        return

    user_data = get_user(user_id)

    min_bet = min(AVAILABLE_BETS['🎯 Рулетка'])
    if user_data['balance'] < min_bet:
        bot.send_message(message.chat.id,
                         f"❌ Недостаточно монет! Минимальная ставка: {min_bet} монет\n💡 Используйте команду '🎁 Бонус' для пополнения баланса")
        return

    bot.send_message(
        message.chat.id,
        f"🎯 РУЛЕТКА\n\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"💵 Выберите размер ставки:",
        reply_markup=create_bet_keyboard('🎯 Рулетка')
    )


# 🔘 ОБРАБОТКА ВЫБОРА СТАВКИ
@bot.callback_query_handler(func=lambda call: call.data.startswith('bet_'))
def handle_bet_selection(call):
    user_id = call.from_user.id
    username = call.from_user.username

    try:
        _, game_type, bet_amount = call.data.split('_')
        bet_amount = int(bet_amount)

        user_data = get_user(user_id)

        if user_data['balance'] < bet_amount:
            bot.answer_callback_query(call.id, f"❌ Недостаточно монет! Нужно {bet_amount}")
            return

        # Удаляем сообщение со ставками
        bot.delete_message(call.message.chat.id, call.message.message_id)

        # Анимация принятия ставки
        loading_msg = bot.send_message(call.message.chat.id, f"🎯 Принимаем ставку {bet_amount} монет...")
        time.sleep(1)
        bot.edit_message_text(f"✅ Ставка {bet_amount} монет принята!", call.message.chat.id, loading_msg.message_id)
        time.sleep(1)
        bot.delete_message(call.message.chat.id, loading_msg.message_id)

        # Запускаем игру
        if game_type == '🎰 Слоты':
            play_slots(call.message.chat.id, user_id, bet_amount)
        elif game_type == '🎲 Кости':
            play_dice(call.message.chat.id, user_id, bet_amount)
        elif game_type == '🎯 Рулетка':
            play_roulette(call.message.chat.id, user_id, bet_amount)

        bot.answer_callback_query(call.id, f"✅ Ставка {bet_amount} принята!")

    except Exception as e:
        print(f"Ошибка в обработке ставки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при обработке ставки")


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_bet')
def handle_cancel_bet(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "❌ Ставка отменена", reply_markup=create_main_keyboard())
    bot.answer_callback_query(call.id, "❌ Ставка отменена")


# 🎯 ФУНКЦИИ ИГР С АНИМАЦИЯМИ
def play_slots(chat_id, user_id, bet):
    user_data = get_user(user_id)

    # Анимация запуска слотов
    start_msg = bot.send_message(chat_id, "🎰 ЗАПУСКАЕМ СЛОТ-МАШИНУ...")
    time.sleep(1)

    # Анимация вращения барабанов
    spin_frames = [
        "🎰 Барабаны крутятся... | 🍒 | 🍋 | 🍊",
        "🎰 Барабаны крутятся... 🍒 | 🍋 | 🍊 |",
        "🎰 Барабаны крутятся... | 🍒 | 🍋 | 🍊 |",
        "🎰 Барабаны замедляются... 🍒 | 🍋 | 🍊",
        "🎰 Почти готово... | 🍒 | 🍋 | 🍊"
    ]

    for frame in spin_frames:
        bot.edit_message_text(frame, chat_id, start_msg.message_id)
        time.sleep(0.5)

    # Генерация результата
    symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
    result = [random.choice(symbols) for _ in range(3)]

    payout = 0

    # 🎰 УМЕНЬШЕННЫЕ ШАНСЫ
    if result[0] == result[1] == result[2]:
        if result[0] == '7️⃣' and random.random() < 0.3:
            payout = bet * 50
        elif result[0] == '💎' and random.random() < 0.4:
            payout = bet * 20
        elif random.random() < 0.5:
            payout = bet * 5
        else:
            payout = 0
    elif (result[0] == result[1] or result[1] == result[2]) and random.random() < 0.4:
        payout = bet * 2
    else:
        payout = 0

    # Дополнительный шанс проигрыша
    if payout > 0 and random.random() < 0.5:
        payout = 0

    # Анимация результата
    bot.edit_message_text(f"🎰 РЕЗУЛЬТАТ: {' | '.join(result)}", chat_id, start_msg.message_id)
    time.sleep(1)

    new_balance = update_balance(user_id, payout - bet)

    # Анимация выигрыша/проигрыша
    if payout > 0:
        win_frames = [
            f"🎉 ВЫИГРЫШ! +{payout} монет!",
            f"💰 ВЫИГРЫШ! +{payout} монет! 💰",
            f"🎊 ВЫИГРЫШ! +{payout} монет! 🎊"
        ]
        if payout >= bet * 10:
            win_frames.append("🔥 ДЖЕКПОТ! 🔥")

        for frame in win_frames:
            bot.edit_message_text(frame, chat_id, start_msg.message_id)
            time.sleep(0.7)
    else:
        lose_frames = [
            "😢 ПРОИГРЫШ...",
            "💸 ПРОИГРЫШ... 💸",
            "❌💀 ПРОИГРЫШ... 💀❌"
        ]
        for frame in lose_frames:
            bot.edit_message_text(frame, chat_id, start_msg.message_id)
            time.sleep(0.7)

    # Финальное сообщение
    message_text = f"🎰 СЛОТ-МАШИНА 🎰\n\n"
    message_text += f"💵 Ставка: {bet} монет\n"
    message_text += f"🎯 Результат: {' | '.join(result)}\n\n"

    if payout > 0:
        message_text += f"🎉 ВЫИГРЫШ! +{payout} монет!\n"
        if payout >= bet * 10:
            message_text += "🔥 ДЖЕКПОТ! 🔥\n"
    else:
        message_text += "😢 ПРОИГРЫШ\n"

    message_text += f"💰 Баланс: {new_balance} монет"

    bot.edit_message_text(message_text, chat_id, start_msg.message_id)


def play_dice(chat_id, user_id, bet):
    user_data = get_user(user_id)

    # Анимация броска костей
    throw_msg = bot.send_message(chat_id, "🎲 БРОСАЕМ КОСТИ...")
    time.sleep(1)

    # Анимация летающих костей
    dice_frames = [
        "🎲 Кости в воздухе... ⚀ ⚁",
        "🎲 Кости крутятся... ⚂ ⚃",
        "🎲 Кости падают... ⚄ ⚅",
        "🎲 Почти упали... ⚀ ⚁",
        "🎲 Результат..."
    ]

    for frame in dice_frames:
        bot.edit_message_text(frame, chat_id, throw_msg.message_id)
        time.sleep(0.4)

    # Генерация результата
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2

    payout = 0

    if total == 7 and random.random() < 0.4:
        payout = bet * 3
        message_text = "🎉 Счастливая 7! x3"
    elif total >= 10 and random.random() < 0.3:
        payout = bet * 2
        message_text = "👍 Больше 9! x2"
    elif total <= 4 and random.random() < 0.3:
        payout = bet * 2
        message_text = "👎 Меньше 5! x2"
    else:
        message_text = "😐 Стандартный бросок"
        payout = 0

    if payout > 0 and random.random() < 0.4:
        payout = 0
        message_text = "💸 УДАЧА ИЗМЕНИЛА"

    # Показываем результат с анимацией
    bot.edit_message_text(f"🎲 РЕЗУЛЬТАТ: {dice1} + {dice2} = {total}", chat_id, throw_msg.message_id)
    time.sleep(1)

    new_balance = update_balance(user_id, payout - bet)

    # Анимация результата
    if payout > 0:
        result_frames = [
            f"🎉 {message_text}",
            f"💰 {message_text} 💰",
            f"🎊 {message_text} 🎊"
        ]
        for frame in result_frames:
            bot.edit_message_text(frame, chat_id, throw_msg.message_id)
            time.sleep(0.6)
    else:
        result_frames = [
            f"😢 {message_text}💀",
            f"💸 {message_text} 💸",
            f"❌💀 {message_text} 💀❌"
        ]
        for frame in result_frames:
            bot.edit_message_text(frame, chat_id, throw_msg.message_id)
            time.sleep(0.6)

    # Финальное сообщение
    result_message = f"🎲 КОСТИ 🎲\n\n"
    result_message += f"💵 Ставка: {bet} монет\n"
    result_message += f"🎯 Бросок: {dice1} + {dice2} = {total}\n"
    result_message += f"📢 {message_text}\n\n"
    result_message += f"💰 Баланс: {new_balance} монет"

    bot.edit_message_text(result_message, chat_id, throw_msg.message_id)


def play_roulette(chat_id, user_id, bet):
    user_data = get_user(user_id)

    # Анимация запуска рулетки
    spin_msg = bot.send_message(chat_id, "🎯 ЗАПУСКАЕМ РУЛЕТКУ...")
    time.sleep(1)

    # Анимация вращения рулетки
    roulette_frames = [
        "🎡 Шар запущен... 🔴",
        "🎡 Шар кружится... ⚫",
        "🎡 Шар замедляется... 🔴",
        "🎡 Почти остановился... ⚫",
        "🎡 Результат..."
    ]

    for frame in roulette_frames:
        bot.edit_message_text(frame, chat_id, spin_msg.message_id)
        time.sleep(0.6)

    # Генерация результата
    number = random.randint(0, 36)
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

    payout = 0
    random_factor = random.random()

    if number == 0:
        if random_factor < 0.018:
            payout = bet * 35
            win_type = "🟢 НЕВЕРОЯТНО! ЗЕЛЕНЫЙ 0!"
        else:
            payout = 0
            win_type = "💸 НОЛЬ НЕ СЫГРАЛ"
    elif number in red_numbers:
        if random_factor < 0.324:
            payout = bet * 2
            win_type = "🔴 КРАСНЫЙ ВЫИГРАЛ"
        else:
            payout = 0
            win_type = "❌ КРАСНЫЙ ПРОИГРАЛ"
    elif number in black_numbers:
        if random_factor < 0.324:
            payout = bet * 2
            win_type = "⚫ ЧЕРНЫЙ ВЫИГРАЛ"
        else:
            payout = 0
            win_type = "❌ ЧЕРНЫЙ ПРОИГРАЛ"

    if payout > 0 and random.random() < 0.6:
        payout = 0
        win_type = "💀 УДАЧА ОТВЕРНУЛАСЬ"

    if user_data['balance'] > 2000 and random.random() < 0.4:
        payout = 0
        win_type = "🏦 БАНК ЗАБИРАЕТ ВСЁ"

    # Показываем результат
    bot.edit_message_text(f"🎡 ВЫПАЛО ЧИСЛО: {number}", chat_id, spin_msg.message_id)
    time.sleep(1)

    new_balance = update_balance(user_id, payout - bet)

    if payout > 0:
        user_data['recent_wins'] = user_data.get('recent_wins', 0) + 1
    else:
        user_data['recent_wins'] = 0

    # Анимация результата
    if payout > 0:
        result_frames = [
            f"🎉 {win_type}",
            f"💰 {win_type} 💰",
            f"🎊 {win_type} 🎊"
        ]
        for frame in result_frames:
            bot.edit_message_text(frame, chat_id, spin_msg.message_id)
            time.sleep(0.7)
    else:
        result_frames = [
            f"😢 {win_type}💀",
            f"💸 {win_type} 💸",
            f"❌💀 {win_type} 💀❌"
        ]
        for frame in result_frames:
            bot.edit_message_text(frame, chat_id, spin_msg.message_id)
            time.sleep(0.7)

    # Финальное сообщение
    result_message = f"🎯 РУЛЕТКА 🎯\n\n"
    result_message += f"💵 Ставка: {bet} монет\n"
    result_message += f"🎡 Выпало: {number}\n"
    result_message += f"📢 {win_type}\n\n"
    result_message += f"💰 Выигрыш: {payout} монет\n"
    result_message += f"💳 Баланс: {new_balance} монет"

    bot.edit_message_text(result_message, chat_id, spin_msg.message_id)


def start_bot():
    print("🎰 Запуск казино-бота с анимациями...")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"🚫 Забаненные: {BANNED_USER_IDS}")
    print(f"🎁 Бонус: +{BONUS_AMOUNT} монет каждые 3 часа")
    print("💵 Доступные ставки:")
    for game, bets in AVAILABLE_BETS.items():
        print(f"  {game}: {bets}")

    while True:
        try:
            print("🔗 Подключаемся к Telegram API...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)


if __name__ == "__main__":
    start_bot()