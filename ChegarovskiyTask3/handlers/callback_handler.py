"""
Обработчик callback-запросов от inline-кнопок
Содержит логику взаимодействия для игр с кнопками
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from keyboards import get_back_keyboard, get_main_keyboard, get_roulette_color_keyboard, get_roulette_even_odd_keyboard, get_blackjack_keyboard
from games import Blackjack
from utils.validator import InputValidator

logger = logging.getLogger(__name__)
db = Database()
validator = InputValidator()

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главный обработчик callback-запросов"""
    query = update.callback_query
    data = query.data
    
    try:
        await query.answer()
        
        if data == "back_to_main":
            await _handle_back_to_main(query)
        elif data.startswith("dice_"):
            await _handle_dice_callback(query, context, data[5:])
        elif data.startswith("bj_"):
            await _handle_blackjack_callback(query, context, data[3:])
        elif data.startswith("roulette_"):
            await _handle_roulette_callback(query, context, data[9:])
        elif data.startswith("color_"):
            await _handle_roulette_color(query, context, data[6:])
        elif data.startswith("even_odd_"):
            await _handle_roulette_even_odd(query, context, data[9:])
            
    except Exception as error:
        logger.error(f"Callback error: {error}")
        await query.answer("❌ Произошла ошибка")

async def _handle_back_to_main(query):
    """Обработать возврат в главное меню"""
    await query.edit_message_text("🏠 Главное меню\n\nВыберите игру:", reply_markup=None)
    await query.message.reply_text("🎰 Добро пожаловать в казино!", reply_markup=get_main_keyboard())

async def _handle_dice_callback(query, context: ContextTypes.DEFAULT_TYPE, bet_type: str):
    """Обработать callback для игры в кости"""
    context.user_data["dice_bet_type"] = bet_type
    context.user_data["current_game"] = "dice"
    
    if bet_type == "number":
        await query.edit_message_text(
            "🎲 Кости | Ставка на число\nВведите число от 2 до 12:",
            reply_markup=get_back_keyboard()
        )
    else:
        bet_description = "чёт" if bet_type == "even" else "нечёт" if bet_type == "odd" else "дубль"
        await query.edit_message_text(
            f"🎲 Кости | Ставка на {bet_description}\nВведите сумму ставки:",
            reply_markup=get_back_keyboard()
        )

async def _handle_roulette_callback(query, context: ContextTypes.DEFAULT_TYPE, bet_type: str):
    """Обработать callback для игры в рулетку"""
    context.user_data["roulette_bet_type"] = bet_type
    context.user_data["current_game"] = "roulette"
    
    if bet_type == "number":
        await query.edit_message_text(
            "🎡 Рулетка | Ставка на число\nВведите число от 0 до 36:",
            reply_markup=get_back_keyboard()
        )
    elif bet_type == "color":
        await query.edit_message_text(
            "🎡 Рулетка | Ставка на цвет\nВыберите цвет:",
            reply_markup=get_roulette_color_keyboard()
        )
    elif bet_type == "even_odd":
        await query.edit_message_text(
            "🎡 Рулетка | Ставка на чёт/нечёт\nВыберите вариант:",
            reply_markup=get_roulette_even_odd_keyboard()
        )

async def _handle_roulette_color(query, context: ContextTypes.DEFAULT_TYPE, color: str):
    """Обработать выбор цвета в рулетке"""
    context.user_data["roulette_bet_value"] = color
    color_name = "красное" if color == "red" else "чёрное"
    await query.edit_message_text(
        f"🎡 Рулетка | Ставка на {color_name}\nВведите сумму ставки:",
        reply_markup=get_back_keyboard()
    )

async def _handle_roulette_even_odd(query, context: ContextTypes.DEFAULT_TYPE, choice: str):
    """Обработать выбор чёт/нечёт в рулетке"""
    context.user_data["roulette_bet_value"] = choice
    choice_name = "чёт" if choice == "even" else "нечёт"
    await query.edit_message_text(
        f"🎡 Рулетка | Ставка на {choice_name}\nВведите сумму ставки:",
        reply_markup=get_back_keyboard()
    )

async def _handle_blackjack_callback(query, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Обработать callback для игры в блекджек"""
    bj_data = context.user_data.get("blackjack")
    if not bj_data:
        await query.edit_message_text("❌ Игра не найдена")
        return
    
    game = bj_data["game"]
    user_id = bj_data["user_id"]
    bet = bj_data["bet"]
    
    if action == "hit":
        await _handle_blackjack_hit(query, context, game, user_id, bet)
    elif action == "stand":
        await _handle_blackjack_stand(query, context, game, user_id, bet)

async def _handle_blackjack_hit(query, context: ContextTypes.DEFAULT_TYPE, 
                              game: Blackjack, user_id: int, bet: int):
    """Обработать действие 'взять карту' в блекджеке"""
    card = game.player_hit()
    player_value = game.calculate_hand_value(game.player_hand)
    
    if player_value > 21:
        db.update_balance(user_id, -bet, "blackjack")
        user_data = db.get_user(user_id)
        
        player_hand_str = " ".join(f"{value}{suit}" for value, suit in game.player_hand)
        await query.edit_message_text(
            f"🃏 Блекджек | Ставка: {bet} монет\n\n"
            f"💼 Дилер: ???\n"
            f"👤 Ваша рука: {player_hand_str} (очки: {player_value} - ПЕРЕБОР!)\n\n"
            f"❌ Вы проиграли!\n"
            f"💰 Баланс: {user_data['balance']} монет",
            reply_markup=get_back_keyboard()
        )
        context.user_data.pop("blackjack", None)
    else:
        await show_blackjack_state(query, context, "Ваш ход:")

async def _handle_blackjack_stand(query, context: ContextTypes.DEFAULT_TYPE,
                                game: Blackjack, user_id: int, bet: int):
    """Обработать действие 'остановиться' в блекджеке"""
    game.dealer_play()
    result, net_change = game.get_game_result()
    
    db.update_balance(user_id, net_change, "blackjack")
    user_data = db.get_user(user_id)
    
    player_hand_str = " ".join(f"{value}{suit}" for value, suit in game.player_hand)
    dealer_hand_str = " ".join(f"{value}{suit}" for value, suit in game.dealer_hand)
    
    result_messages = {
        "win": "🎉 Вы выиграли!",
        "lose": "❌ Вы проиграли!",
        "push": "🤝 Ничья!"
    }
    
    await query.edit_message_text(
        f"🃏 Блекджек | Ставка: {bet} монет\n\n"
        f"💼 Дилер: {dealer_hand_str} (очки: {game.dealer_value})\n"
        f"👤 Ваша рука: {player_hand_str} (очки: {game.player_value})\n\n"
        f"**{result_messages[result]}**\n"
        f"💰 Баланс: {user_data['balance']} монет",
        reply_markup=get_back_keyboard()
    )
    context.user_data.pop("blackjack", None)

async def show_blackjack_state(update, context: ContextTypes.DEFAULT_TYPE, message: str = ""):
    """Показать текущее состояние игры в блекджек"""
    bj_data = context.user_data["blackjack"]
    game = bj_data["game"]
    
    player_value = game.calculate_hand_value(game.player_hand)
    dealer_visible_value = game.calculate_hand_value([game.dealer_hand[0]])
    
    player_hand_str = " ".join(f"{value}{suit}" for value, suit in game.player_hand)
    dealer_hand_str = f"{game.dealer_hand[0][0]}{game.dealer_hand[0][1]} ??"
    
    state_text = (f"🃏 Блекджек | Ставка: {bj_data['bet']} монет\n\n"
                  f"💼 Дилер: {dealer_hand_str} (очки: {dealer_visible_value}+?)\n"
                  f"👤 Ваша рука: {player_hand_str} (очки: {player_value})\n\n"
                  f"{message}")
    
    markup = get_blackjack_keyboard()
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(state_text, reply_markup=markup)
    else:
        await update.message.reply_text(state_text, reply_markup=markup)
