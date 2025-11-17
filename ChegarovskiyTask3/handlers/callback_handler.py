"""Обработчики callback-запросов"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from keyboards import (
    get_back_keyboard, get_dice_bet_keyboard, get_blackjack_keyboard,
    get_roulette_bet_keyboard, get_roulette_color_keyboard, get_roulette_even_odd_keyboard
)
from games.dice import DiceGame
from games.blackjack import Blackjack
from games.roulette import Roulette
from config import EMOJI

logger = logging.getLogger(__name__)
db = Database()

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
            from keyboards import get_main_keyboard
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

# ===== BLACKJACK LOGIC =====
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
            from handlers.bet_handler import show_blackjack_state
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

    # Сохраняем тип ставки для костей
    context.user_data["dice_bet_type"] = bet_type
    context.user_data["current_game"] = "dice"

    if bet_type == "number":
        context.user_data["dice_waiting_for_number"] = True
        await query.edit_message_text(
            "🎲 **КОСТИ** | Ставка на число\n\n"
            "Введите число от 2 до 12:",
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

    # Сохраняем тип ставки для рулетки
    context.user_data["roulette_bet_type"] = bet_type
    context.user_data["current_game"] = "roulette"

    if bet_type == "number":
        context.user_data["roulette_waiting_for_number"] = True
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

    # Определяем цвет выпавшего числа
    color_emoji = "🔴" if winning_number in Roulette.RED_NUMBERS else "⚫"
    if winning_number == 0:
        color_emoji = "🟢"

    result_text = (
        f"🎡 **РУЛЕТКА** | Ставка: {bet_amount} на {bet_description}\n\n"
        f"Выпало: {winning_number} {color_emoji}\n"
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

async def handle_roulette_color(update: Update, context: ContextTypes.DEFAULT_TYPE, color: str) -> None:
    """Обработать выбор цвета в рулетке"""
    query = update.callback_query
    await query.answer()

    context.user_data["roulette_bet_value"] = color
    context.user_data["current_game"] = "roulette"

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
    context.user_data["current_game"] = "roulette"

    await query.edit_message_text(
        f"🎡 **РУЛЕТКА** | Ставка на {'чёт' if choice == 'even' else 'нечёт'}\n\n"
        "Введите сумму ставки:",
        reply_markup=get_back_keyboard()
    )

def get_blackjack_keyboard():
    """Функция для импорта клавиатуры блекджека"""
    from keyboards import get_blackjack_keyboard as kb
    return kb()