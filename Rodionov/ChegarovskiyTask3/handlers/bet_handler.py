"""
Главный обработчик текстовых сообщений для игр
Использует Validator для проверки ввода и игры для логики
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from games import SlotMachine, DiceGame, Blackjack, Roulette
from keyboards import get_back_keyboard
from utils.validator import InputValidator

db = Database()
validator = InputValidator()

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Обработать все текстовые сообщения для игрового процесса"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("❌ Сначала используйте /start")
        return
    
    try:
        number = await validator.validate_number_input(update, update.message.text)
    except ValueError:
        return
    
    await _process_game_input(update, context, user.id, number, user_data['balance'])

async def _process_game_input(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            user_id: int, number: int, user_balance: int):
    """Обработать игровой ввод на основе контекста"""
    if "dice_bet_type" in context.user_data:
        await _handle_dice_input(update, context, user_id, number, user_balance)
    elif "roulette_bet_type" in context.user_data:
        await _handle_roulette_input(update, context, user_id, number, user_balance)
    elif context.user_data.get("current_game") == "slots":
        await _handle_slots_game(update, context, user_id, number, user_balance)
    elif context.user_data.get("current_game") == "blackjack":
        await _start_blackjack_game(update, context, user_id, number, user_balance)
    else:
        await update.message.reply_text("❌ Сначала выберите игру!")

async def _handle_dice_input(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           user_id: int, number: int, user_balance: int):
    """Обработать ввод для игры в кости"""
    bet_type = context.user_data["dice_bet_type"]
    
    if bet_type == "number" and "dice_number" not in context.user_data:
        if not await validator.validate_game_input(update, "dice_number", number):
            return
        context.user_data["dice_number"] = number
        await update.message.reply_text(
            f"🎲 Ставка на число {number}\nВведите сумму ставки:",
            reply_markup=get_back_keyboard()
        )
    else:
        await _process_dice_game(update, context, user_id, number, user_balance)

async def _process_dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           user_id: int, bet_amount: int, user_balance: int):
    """Сыграть в кости"""
    if not await validator.validate_bet_amount(update, user_balance, bet_amount):
        return
    
    bet_type = context.user_data["dice_bet_type"]
    number = context.user_data.get("dice_number")
    
    game = DiceGame()
    dice1, dice2, total, win_amount = game.play(bet_amount, bet_type, number)
    net_change = win_amount - bet_amount
    
    result_text = _format_dice_result(bet_amount, bet_type, number, dice1, dice2, total, win_amount)
    await _process_game_result(update, context, user_id, net_change, "dice", result_text)

async def _handle_roulette_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               user_id: int, number: int, user_balance: int):
    """Обработать ввод для игры в рулетку"""
    bet_type = context.user_data["roulette_bet_type"]
    
    if bet_type == "number" and "roulette_bet_value" not in context.user_data:
        if not await validator.validate_game_input(update, "roulette_number", number):
            return
        context.user_data["roulette_bet_value"] = number
        await update.message.reply_text(
            f"🎡 Ставка на число {number}\nВведите сумму ставки:",
            reply_markup=get_back_keyboard()
        )
    else:
        await _process_roulette_game(update, context, user_id, number, user_balance)

async def _process_roulette_game(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               user_id: int, bet_amount: int, user_balance: int):
    """Сыграть в рулетку"""
    if not await validator.validate_bet_amount(update, user_balance, bet_amount):
        return
    
    bet_type = context.user_data["roulette_bet_type"]
    bet_value = context.user_data.get("roulette_bet_value")
    
    game = Roulette()
    winning_number, win_amount = game.play(bet_amount, bet_type, bet_value)
    net_change = win_amount - bet_amount
    
    result_text = _format_roulette_result(bet_amount, bet_type, bet_value, winning_number, win_amount, game)
    await _process_game_result(update, context, user_id, net_change, "roulette", result_text)

async def _handle_slots_game(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           user_id: int, bet_amount: int, user_balance: int):
    """Сыграть в слоты"""
    if not await validator.validate_bet_amount(update, user_balance, bet_amount):
        return
    
    game = SlotMachine()
    reels, multiplier = game.play(bet_amount)
    win_amount = game.get_win_amount()
    net_change = win_amount - bet_amount
    
    result_text = _format_slots_result(reels, bet_amount, win_amount, multiplier)
    await _process_game_result(update, context, user_id, net_change, "slots", result_text)

async def _start_blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              user_id: int, bet: int, user_balance: int):
    """Начать игру в блекджек"""
    if not await validator.validate_bet_amount(update, user_balance, bet):
        return
    
    game = Blackjack()
    player_hand, dealer_hand = game.play(bet)
    
    context.user_data["blackjack"] = {
        "game": game,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "bet": bet,
        "user_id": user_id
    }
    
    from handlers.callback_handler import show_blackjack_state
    await show_blackjack_state(update, context, "Ваш ход:")

async def _process_game_result(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             user_id: int, net_change: int, game_type: str, result_text: str):
    """Обработать и показать результат игры"""
    db.update_balance(user_id, net_change, game_type)
    user_data = db.get_user(user_id)
    
    final_text = f"{result_text}\n💰 Баланс: {user_data['balance']} монет"
    await update.message.reply_text(final_text, reply_markup=get_back_keyboard())
    _clear_game_context(context, game_type)

def _clear_game_context(context: ContextTypes.DEFAULT_TYPE, game_type: str):
    #Ошибка: Очистка неполная, могут остаться данные
    """Очистить игровой контекст"""
    context_data_map = {
        "dice": ["dice_bet_type", "dice_number"],
        "roulette": ["roulette_bet_type", "roulette_bet_value"],
        "slots": ["current_game"],
        "blackjack": ["current_game", "blackjack"]
    }
    
    for key in context_data_map.get(game_type, []):
        context.user_data.pop(key, None)

def _format_dice_result(bet_amount: int, bet_type: str, number: int, 
                       dice1: int, dice2: int, total: int, win_amount: int) -> str:
    """Форматировать результат игры в кости"""
    bet_descriptions = {
        "number": f"число {number}",
        "even": "чёт", "odd": "нечёт", "double": "дубль"
    }
    
    description = bet_descriptions.get(bet_type, "неизвестная ставка")
    result_emoji = "🎉" if win_amount > 0 else "😞"
    result_text = "Поздравляем с выигрышем!" if win_amount > 0 else "Повезёт в следующий раз!"
    
    return (f"🎲 Кости | Ставка: {bet_amount} на {description}\n\n"
            f"Результат: {dice1} + {dice2} = {total}\n"
            f"Выигрыш: {win_amount} монет\n\n"
            f"{result_emoji} {result_text}")

def _format_roulette_result(bet_amount: int, bet_type: str, bet_value: int,
                          winning_number: int, win_amount: int, game: Roulette) -> str:
    """Форматировать результат игры в рулетку"""
    bet_descriptions = {
        "number": f"число {bet_value}",
        "color": f"{'красное' if bet_value == 'red' else 'чёрное'}",
        "even_odd": f"{'чёт' if bet_value == 'even' else 'нечёт'}"
    }
    
    color_emoji = "🟢" if winning_number == 0 else "🔴" if winning_number in Roulette.RED_NUMBERS else "⚫"
    description = bet_descriptions.get(bet_type, "неизвестная ставка")
    result_emoji = "🎉" if win_amount > 0 else "😞"
    result_text = "Поздравляем с выигрышем!" if win_amount > 0 else "Повезёт в следующий раз!"
    
    return (f"🎡 Рулетка | Ставка: {bet_amount} на {description}\n\n"
            f"Выпало: {winning_number} {color_emoji}\n"
            f"Выигрыш: {win_amount} монет\n\n"
            f"{result_emoji} {result_text}")

def _format_slots_result(reels: list, bet_amount: int, win_amount: int, multiplier: int) -> str:
    """Форматировать результат игры в слоты"""
    reels_display = " ".join(f"[{symbol}]" for symbol in reels)
    
    if multiplier == 5:
        result_text = "🎉 ДЖЕКПОТ! 3 одинаковых символа!"
    elif multiplier == 2:
        result_text = "👍 Хорошо! 2 одинаковых символа!"
    else:
        result_text = "😞 Повезёт в следующий раз!"
    
    return (f"🎰 Слот-машина\n\n"
            f"Результат: {reels_display}\n"
            f"Ставка: {bet_amount} монет\n"
            f"Выигрыш: {win_amount} монет\n"
            f"**{result_text}**")
