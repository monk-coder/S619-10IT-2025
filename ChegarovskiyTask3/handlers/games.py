"""Обработчики игр и callback-запросов"""
import logging
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import Database
from keyboards import (
    get_back_keyboard, get_dice_bet_keyboard, get_blackjack_keyboard,
    get_roulette_bet_keyboard, get_roulette_color_keyboard, get_roulette_even_odd_keyboard
)
from games.slots import SlotMachine
from games.dice import DiceGame
from games.blackjack import Blackjack
from games.roulette import Roulette
from config import EMOJI

logger = logging.getLogger(__name__)
db = Database()

# ===== ОБРАБОТЧИКИ ЗАПУСКА ИГР =====
async def start_slots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в слоты"""
    await update.message.reply_text(
        "🎰 **ИГРА: СЛОТ-МАШИНА**\n\n"
        "Введите сумму ставки (целое число):",
        reply_markup=get_back_keyboard()
    )
    context.user_data["game"] = "slots"

async def start_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в кости"""
    await update.message.reply_text(
        "🎲 **ИГРА: КОСТИ**\n\n"
        "Выберите тип ставки:",
        reply_markup=get_dice_bet_keyboard()
    )

async def start_blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в блекджек"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if not user_data:
        await update.message.reply_text("❌ Сначала используйте /start")
        return

    await update.message.reply_text(
        "🃏 **ИГРА: БЛЕКДЖЕК**\n\n"
        "Введите сумму ставки (целое число):",
        reply_markup=get_back_keyboard()
    )
    context.user_data["game"] = "blackjack"

async def start_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать игру в рулетку"""
    await update.message.reply_text(
        "🎡 **ИГРА: РУЛЕТКА**\n\n"
        "Выберите тип ставки:",
        reply_markup=get_roulette_bet_keyboard()
    )

# ===== ОБРАБОТЧИКИ СТАВОК =====
async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать ставку от пользователя"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    game_type = context.user_data.get("game")

    if not user_data or not game_type:
        await update.message.reply_text("❌ Ошибка. Начните игру заново.")
        return

    try:
        bet_amount = int(update.message.text)
        if bet_amount <= 0:
            await update.message.reply_text("❌ Ставка должна быть положительным числом!")
            return
        if bet_amount > user_data['balance']:
            await update.message.reply_text("❌ Недостаточно средств на балансе!")
            return
    except ValueError:
        await update.message.reply_text("❌ Введите целое число!")
        return

    context.user_data["bet"] = bet_amount

    if game_type == "slots":
        await play_slots(update, context, user.id, bet_amount)
    elif game_type == "blackjack":
        await start_blackjack_game(update, context, user.id, bet_amount)

async def play_slots(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bet: int) -> None:
    """Играть в слоты"""
    reels, multiplier = SlotMachine.spin()
    win_amount = bet * multiplier if multiplier > 0 else 0
    net_change = win_amount - bet

    # Обновить баланс
    db.update_balance(user_id, net_change, "slots")
    user_data = db.get_user(user_id)

    # Форматирование результата
    reels_display = " ".join(f"[{symbol}]" for symbol in reels)

    if multiplier == 5:
        result_text = "🎉 ДЖЕКПОТ! 3 одинаковых символа!"
    elif multiplier == 2:
        result_text = "👍 Хорошо! 2 одинаковых символа!"
    else:
        result_text = "😞 Повезёт в следующий раз!"

    message = (
        f"🎰 **СЛОТ-МАШИНА**\n\n"
        f"Результат: {reels_display}\n"
        f"Ставка: {bet} монет\n"
        f"Выигрыш: {win_amount} монет\n"
        f"**{result_text}**\n\n"
        f"💰 Новый баланс: {user_data['balance']} монет"
    )

    await update.message.reply_text(message, reply_markup=get_back_keyboard())

# ===== BLACKJACK LOGIC =====
async def start_blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bet: int) -> None:
    """Начать игру в блекджек"""
    game = Blackjack()

    # Раздать начальные карты
    player_hand = [game.deal_card(), game.deal_card()]
    dealer_hand = [game.deal_card(), game.deal_card()]

    # Сохранить состояние игры
    context.user_data["blackjack"] = {
        "game": game,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "bet": bet,
        "user_id": user_id
    }

    await show_blackjack_state(update, context, "Ваш ход:")

async def show_blackjack_state(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = "") -> None:
    """Показать текущее состояние игры в блекджек"""
    bj_data = context.user_data["blackjack"]
    game = bj_data["game"]
    player_hand = bj_data["player_hand"]
    dealer_hand = bj_data["dealer_hand"]

    player_value = game.calculate_hand_value(player_hand)
    dealer_visible_value = game.calculate_hand_value([dealer_hand[0]])

    player_hand_str = " ".join(f"{value}{suit}" for value, suit in player_hand)
    dealer_hand_str = f"{dealer_hand[0][0]}{dealer_hand[0][1]} ??"

    state_text = (
        f"🃏 **БЛЕКДЖЕК** | Ставка: {bj_data['bet']} монет\n\n"
        f"💼 **Дилер:** {dealer_hand_str} (очки: {dealer_visible_value}+?)\n"
        f"👤 **Ваша рука:** {player_hand_str} (очки: {player_value})\n\n"
        f"{message}"
    )

    # Используем правильный метод для callback или message
    if update.callback_query:
        await update.callback_query.edit_message_text(state_text, reply_markup=get_blackjack_keyboard())
    else:
        await update.message.reply_text(state_text, reply_markup=get_blackjack_keyboard())

async def handle_blackjack_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """Обработать действие в блекджеке"""
    query = update.callback_query
    await query.answer()

    bj_data = context.user_data.get("blackjack")
    if not bj_data:
        await query.edit_message_text("❌ Игра не найдена. Начните заново.")
        return

    game = bj_data["game"]
    player_hand = bj_data["player_hand"]
    dealer_hand = bj_data["dealer_hand"]
    bet = bj_data["bet"]
    user_id = bj_data["user_id"]

    if action == "bj_hit":
        # Игрок берёт карту
        player_hand.append(game.deal_card())
        player_value = game.calculate_hand_value(player_hand)

        if player_value > 21:
            # Перебор - игрок проиграл
            db.update_balance(user_id, -bet, "blackjack")
            user_data = db.get_user(user_id)

            player_hand_str = " ".join(f"{value}{suit}" for value, suit in player_hand)
            dealer_hand_str = f"{dealer_hand[0][0]}{dealer_hand[0][1]} ??"

            await query.edit_message_text(
                f"🃏 **БЛЕКДЖЕК** | Ставка: {bet} монет\n\n"
                f"💼 **Дилер:** {dealer_hand_str}\n"
                f"👤 **Ваша рука:** {player_hand_str} (очки: {player_value} - ПЕРЕБОР!)\n\n"
                f"❌ Вы проиграли!\n"
                f"💰 Новый баланс: {user_data['balance']} монет",
                reply_markup=get_back_keyboard()
            )
            context.user_data.pop("blackjack", None)
        else:
            bj_data["player_hand"] = player_hand
            await show_blackjack_state(update, context, "Ваш ход:")

    elif action == "bj_stand":
        # Игрок остановился, ход дилера
        dealer_value = game.calculate_hand_value(dealer_hand)

        # Дилер берёт карты до 17 очков
        while dealer_value < 17:
            dealer_hand.append(game.deal_card())
            dealer_value = game.calculate_hand_value(dealer_hand)

        # Определение результата
        player_value = game.calculate_hand_value(player_hand)

        if dealer_value > 21 or player_value > dealer_value:
            result = "win"
            win_amount = bet
            message = "🎉 Вы выиграли!"
        elif player_value < dealer_value:
            result = "lose"
            win_amount = -bet
            message = "❌ Вы проиграли!"
        else:
            result = "push"
            win_amount = 0
            message = "🤝 Ничья!"

        # Обновить баланс
        db.update_balance(user_id, win_amount, "blackjack")
        user_data = db.get_user(user_id)

        player_hand_str = " ".join(f"{value}{suit}" for value, suit in player_hand)
        dealer_hand_str = " ".join(f"{value}{suit}" for value, suit in dealer_hand)

        await query.edit_message_text(
            f"🃏 **БЛЕКДЖЕК** | Ставка: {bet} монет\n\n"
            f"💼 **Дилер:** {dealer_hand_str} (очки: {dealer_value})\n"
            f"👤 **Ваша рука:** {player_hand_str} (очки: {player_value})\n\n"
            f"**{message}**\n"
            f"💰 Новый баланс: {user_data['balance']} монет",
            reply_markup=get_back_keyboard()
        )
        context.user_data.pop("blackjack", None)

# ===== DICE LOGIC =====
async def handle_dice_bet(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type: str) -> None:
    """Обработать ставку в костях"""
    query = update.callback_query
    await query.answer()

    context.user_data["dice_bet_type"] = bet_type

    if bet_type in ["number", "double"]:
        if bet_type == "number":
            await query.edit_message_text(
                "🎲 **КОСТИ** | Ставка на число\n\n"
                "Введите число от 2 до 12:",
                reply_markup=get_back_keyboard()
            )
        else:
            # Для дубля сразу запрашиваем ставку
            await query.edit_message_text(
                "🎲 **КОСТИ** | Ставка на дубль\n\n"
                "Введите сумму ставки:",
                reply_markup=get_back_keyboard()
            )
    else:
        await query.edit_message_text(
            f"🎲 **КОСТИ** | Ставка на {'чёт' if bet_type == 'even' else 'нечёт'}\n\n"
            "Введите сумму ставки:",
            reply_markup=get_back_keyboard()
        )

async def play_dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bet_amount: int, bet_type: str, number: int = None) -> None:
    """Сыграть в кости"""
    dice1, dice2, total, win_amount = DiceGame.roll(bet_amount, bet_type, number)
    net_change = win_amount - bet_amount

    # Обновить баланс
    db.update_balance(user_id, net_change, "dice")
    user_data = db.get_user(user_id)

    # Форматирование результата
    if bet_type == "number":
        bet_description = f"число {number}"
    elif bet_type == "even":
        bet_description = "чёт"
    elif bet_type == "odd":
        bet_description = "нечёт"
    else:  # double
        bet_description = "дубль"

    result_text = (
        f"🎲 **КОСТИ** | Ставка: {bet_amount} на {bet_description}\n\n"
        f"Результат: {dice1} + {dice2} = {total}\n"
        f"Выигрыш: {win_amount} монет\n\n"
    )

    if win_amount > 0:
        result_text += f"🎉 Поздравляем с выигрышем!\n"
    else:
        result_text += f"😞 Повезёт в следующий раз!\n"

    result_text += f"💰 Новый баланс: {user_data['balance']} монет"

    if update.callback_query:
        await update.callback_query.edit_message_text(result_text, reply_markup=get_back_keyboard())
    else:
        await update.message.reply_text(result_text, reply_markup=get_back_keyboard())

# ===== ROULETTE LOGIC =====
async def handle_roulette_bet(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type: str) -> None:
    """Обработать ставку в рулетке"""
    query = update.callback_query
    await query.answer()

    context.user_data["roulette_bet_type"] = bet_type

    if bet_type == "number":
        await query.edit_message_text(
            "🎡 **РУЛЕТКА** | Ставка на число\n\n"
            "Введите число от 0 до 36:",
            reply_markup=get_back_keyboard()
        )
    elif bet_type == "color":
        await query.edit_message_text(
            "🎡 **РУЛЕТКА** | Ставка на цвет\n\n"
            "Выберите цвет:",
            reply_markup=get_roulette_color_keyboard()
        )
    elif bet_type == "even_odd":
        await query.edit_message_text(
            "🎡 **РУЛЕТКА** | Ставка на чёт/нечёт\n\n"
            "Выберите вариант:",
            reply_markup=get_roulette_even_odd_keyboard()
        )

async def play_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bet_amount: int, bet_type: str, bet_value) -> None:
    """Сыграть в рулетку"""
    winning_number = Roulette.spin()
    win_amount = Roulette.calculate_payout(bet_type, bet_value, winning_number) * bet_amount
    net_change = win_amount - bet_amount

    # Обновить баланс
    db.update_balance(user_id, net_change, "roulette")
    user_data = db.get_user(user_id)

    # Форматирование результата
    if bet_type == "number":
        bet_description = f"число {bet_value}"
    elif bet_type == "color":
        bet_description = f"{'красное' if bet_value == 'red' else 'чёрное'}"
    else:  # even_odd
        bet_description = f"{'чёт' if bet_value == 'even' else 'нечёт'}"

    result_text = (
        f"🎡 **РУЛЕТКА** | Ставка: {bet_amount} на {bet_description}\n\n"
        f"Выпало: {winning_number} {'🔴' if winning_number in Roulette.RED_NUMBERS else '⚫'}\n"
        f"Выигрыш: {win_amount} монет\n\n"
    )

    if win_amount > 0:
        result_text += f"🎉 Поздравляем с выигрышем!\n"
    else:
        result_text += f"😞 Повезёт в следующий раз!\n"

    result_text += f"💰 Новый баланс: {user_data['balance']} монет"

    if update.callback_query:
        await update.callback_query.edit_message_text(result_text, reply_markup=get_back_keyboard())
    else:
        await update.message.reply_text(result_text, reply_markup=get_back_keyboard())

# ===== CALLBACK HANDLER =====
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать callback-запросы от inline-кнопок"""
    query = update.callback_query
    data = query.data

    try:
        # Навигация
        if data == "back_to_main":
            await query.edit_message_text(
                "🏠 **Главное меню**\n\nВыберите игру:",
                reply_markup=None
            )
            await query.message.reply_text("🎰 Добро пожаловать в казино!", reply_markup=get_main_keyboard())
            return

        # Обработка игр
        if data.startswith("dice_"):
            await handle_dice_bet(update, context, data[5:])
        elif data.startswith("bj_"):
            await handle_blackjack_action(update, context, data)
        elif data.startswith("roulette_"):
            await handle_roulette_bet(update, context, data[9:])
        elif data.startswith("color_"):
            await handle_roulette_color(update, context, data[6:])
        elif data.startswith("even_odd_"):
            await handle_roulette_even_odd(update, context, data[9:])

    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        await query.answer("❌ Произошла ошибка. Попробуйте снова.")

async def handle_roulette_color(update: Update, context: ContextTypes.DEFAULT_TYPE, color: str) -> None:
    """Обработать выбор цвета в рулетке"""
    query = update.callback_query
    await query.answer()

    context.user_data["roulette_bet_value"] = color
    await query.edit_message_text(
        f"🎡 **РУЛЕТКА** | Ставка на {'красное' if color == 'red' else 'чёрное'}\n\n"
        "Введите сумму ставки:",
        reply_markup=get_back_keyboard()
    )

async def handle_roulette_even_odd(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str) -> None:
    """Обработать выбор чёт/нечёт в рулетке"""
    query = update.callback_query
    await query.answer()

    context.user_data["roulette_bet_value"] = choice
    await query.edit_message_text(
        f"🎡 **РУЛЕТКА** | Ставка на {'чёт' if choice == 'even' else 'нечёт'}\n\n"
        "Введите сумму ставки:",
        reply_markup=get_back_keyboard()
    )


# ===== ОБРАБОТКА ЧИСЛОВЫХ ВВОДОВ ДЛЯ ИГР =====
async def handle_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать числовой ввод для различных игр"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if not user_data:
        await update.message.reply_text("❌ Сначала используйте /start")
        return

    try:
        number = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите целое число!")
        return

    # Проверяем, какая игра активна
    if "dice_bet_type" in context.user_data:
        await handle_dice_number_input(update, context, user.id, number)
    elif "roulette_bet_type" in context.user_data:
        await handle_roulette_number_input(update, context, user.id, number)
    else:
        # Если нет активной игры, передаем в handle_bet
        await handle_bet(update, context)


async def handle_dice_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                                   number: int) -> None:
    """Обработать числовой ввод для костей"""
    bet_type = context.user_data.get("dice_bet_type")

    if bet_type == "number":
        if number < 2 or number > 12:
            await update.message.reply_text("❌ Число должно быть от 2 до 12!")
            return
        context.user_data["dice_number"] = number
        await update.message.reply_text(
            f"🎲 **КОСТИ** | Ставка на число {number}\n\n"
            "Введите сумму ставки:",
            reply_markup=get_back_keyboard()
        )
    else:
        # Для других типов ставок число - это сумма ставки
        await handle_dice_bet_amount(update, context, user_id, number)


async def handle_dice_bet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                                 bet_amount: int) -> None:
    """Обработать сумму ставки для костей"""
    user_data = db.get_user(user_id)
    bet_type = context.user_data.get("dice_bet_type")

    if bet_amount <= 0:
        await update.message.reply_text("❌ Ставка должна быть положительным числом!")
        return
    if bet_amount > user_data['balance']:
        await update.message.reply_text("❌ Недостаточно средств на балансе!")
        return

    if bet_type == "number":
        number = context.user_data.get("dice_number")
        if number is None:
            await update.message.reply_text("❌ Ошибка. Начните заново.")
            return
        await play_dice_game(update, context, user_id, bet_amount, bet_type, number)
    else:
        await play_dice_game(update, context, user_id, bet_amount, bet_type)

    # Очистить временные данные
    context.user_data.pop("dice_bet_type", None)
    context.user_data.pop("dice_number", None)


async def handle_roulette_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                                       number: int) -> None:
    """Обработать числовой ввод для рулетки"""
    bet_type = context.user_data.get("roulette_bet_type")

    if bet_type == "number":
        if number < 0 or number > 36:
            await update.message.reply_text("❌ Число должно быть от 0 до 36!")
            return
        context.user_data["roulette_bet_value"] = number
        await update.message.reply_text(
            f"🎡 **РУЛЕТКА** | Ставка на число {number}\n\n"
            "Введите сумму ставки:",
            reply_markup=get_back_keyboard()
        )
    else:
        # Для других типов ставок число - это сумма ставки
        await handle_roulette_bet_amount(update, context, user_id, number)


async def handle_roulette_bet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                                     bet_amount: int) -> None:
    """Обработать сумму ставки для рулетки"""
    user_data = db.get_user(user_id)
    bet_type = context.user_data.get("roulette_bet_type")
    bet_value = context.user_data.get("roulette_bet_value")

    if bet_amount <= 0:
        await update.message.reply_text("❌ Ставка должна быть положительным числом!")
        return
    if bet_amount > user_data['balance']:
        await update.message.reply_text("❌ Недостаточно средств на балансе!")
        return

    if bet_type and bet_value:
        await play_roulette(update, context, user_id, bet_amount, bet_type, bet_value)

    # Очистить временные данные
    context.user_data.pop("roulette_bet_type", None)
    context.user_data.pop("roulette_bet_value", None)