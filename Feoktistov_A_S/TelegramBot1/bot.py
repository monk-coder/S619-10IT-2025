import random
import telebot
from telebot.types import ReplyKeyboardMarkup

# ✅ Твой токен
BOT_TOKEN = "8277822996:AAHdjF8a3zofwNAyBIeychcI7ZYjmcqik5I"

bot = telebot.TeleBot(BOT_TOKEN)
STARTING_BALANCE = 1000
users_db = {}


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
    keyboard.row('🎲 Кости', '💰 Баланс')
    return keyboard


@bot.message_handler(commands=['start'])
def start_command(message):
    user_data = get_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"🎉 Добро пожаловать в Казино, {message.from_user.first_name}!\n"
        f"💰 Стартовый баланс: {user_data['balance']} монет\n\n"
        "Выберите игру:",
        reply_markup=create_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == '💰 Баланс')
def balance_command(message):
    user_data = get_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {user_data['balance']} монет\n"
        f"🎮 Игр сыграно: {user_data['games_played']}\n"
        f"🏆 Побед: {user_data['wins']}"
    )


@bot.message_handler(func=lambda message: message.text == '🎰 Слоты')
def slots_game(message):
    user_id = message.from_user.id
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


if __name__ == "__main__":
    print("🎰 Казино-бот запущен!")
    print("✅ Бот работает с pyTelegramBotAPI")
    bot.infinity_polling()