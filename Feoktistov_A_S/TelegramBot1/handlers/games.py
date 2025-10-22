import random
from telegram import Update
from telegram.ext import ContextTypes
from database import db


# 🎰 Игровые автоматы
async def slots_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    # Проверка баланса
    if user_data['balance'] < 10:
        await update.message.reply_text("❌ Недостаточно монет! Минимальная ставка: 10")
        return

    # Спин слотов
    symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
    result = [random.choice(symbols) for _ in range(3)]

    # Выигрышные комбинации
    payout = 0
    bet = 10

    if result[0] == result[1] == result[2]:
        if result[0] == '7️⃣':
            payout = bet * 50  # Джекпот!
        elif result[0] == '💎':
            payout = bet * 20
        elif result[0] == '🔔':
            payout = bet * 10
        else:
            payout = bet * 5
    elif result[0] == result[1] or result[1] == result[2]:
        payout = bet * 2

    # Обновление баланса
    new_balance = db.update_balance(user_id, payout - bet)

    # Сообщение с результатом
    message = f"🎰 СЛОТ-МАШИНА 🎰\n\n" \
              f"Результат: {' | '.join(result)}\n\n"

    if payout > 0:
        message += f"🎉 ВЫИГРЫШ! +{payout} монет!\n"
        if payout >= bet * 20:
            message += "🔥 ДЖЕКПОТ! 🔥\n"
    else:
        message += "😢 Повезет в следующий раз!\n"

    message += f"💰 Баланс: {new_balance} монет"

    await update.message.reply_text(message)


# 🎯 Рулетка
async def roulette_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if user_data['balance'] < 20:
        await update.message.reply_text("❌ Недостаточно монет! Минимальная ставка: 20")
        return

    # Простая рулетка
    number = random.randint(0, 36)
    is_red = number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

    bet = 20
    payout = 0

    # Определение выигрыша
    if number == 0:
        message = "🟢 0 - Удача на вашей стороне! x35"
        payout = bet * 35
    elif is_red and number % 2 == 1:
        message = f"🔴 {number} - Красное нечетное! x2"
        payout = bet * 2
    elif not is_red and number % 2 == 0 and number != 0:
        message = f"⚫ {number} - Черное четное! x2"
        payout = bet * 2
    else:
        message = f"⚪ {number} - К сожалению, проигрыш"

    new_balance = db.update_balance(user_id, payout - bet)

    await update.message.reply_text(
        f"🎯 РУЛЕТКА 🎯\n\n"
        f"Выпало: {number}\n"
        f"{message}\n\n"
        f"💰 Баланс: {new_balance} монет"
    )


# 🎲 Кости
async def dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if user_data['balance'] < 15:
        await update.message.reply_text("❌ Недостаточно монет! Минимальная ставка: 15")
        return

    bet = 15
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2

    payout = 0

    if total == 7:
        payout = bet * 3
        message = "🎉 Счастливая 7! x3"
    elif total >= 10:
        payout = bet * 2
        message = f"👍 Больше 9! x2"
    elif total <= 4:
        payout = bet * 2
        message = f"👎 Меньше 5! x2"
    else:
        message = "😐 Стандартный бросок"

    new_balance = db.update_balance(user_id, payout - bet)

    await update.message.reply_text(
        f"🎲 КОСТИ 🎲\n\n"
        f"🎯 Бросок: {dice1} + {dice2} = {total}\n"
        f"{message}\n\n"
        f"💰 Баланс: {new_balance} монет"
    )


# 🃏 Блекджек (упрощенный)
async def blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if user_data['balance'] < 25:
        await update.message.reply_text("❌ Недостаточно монет! Минимальная ставка: 25")
        return

    bet = 25

    user_card = random.randint(1, 11)
    dealer_card = random.randint(1, 11)

    if user_card > dealer_card:
        payout = bet * 2
        message = f"🎉 Вы выиграли! {user_card} > {dealer_card}"
    elif user_card < dealer_card:
        payout = 0
        message = f"😢 Дилер выиграл! {user_card} < {dealer_card}"
    else:
        payout = bet
        message = f"🤝 Ничья! {user_card} = {dealer_card}"

    new_balance = db.update_balance(user_id, payout - bet)

    await update.message.reply_text(
        f"🃏 БЛЕКДЖЕК 🃏\n\n"
        f"Ваша карта: {user_card}\n"
        f"Карта дилера: {dealer_card}\n\n"
        f"{message}\n\n"
        f"💰 Баланс: {new_balance} монет"
    )