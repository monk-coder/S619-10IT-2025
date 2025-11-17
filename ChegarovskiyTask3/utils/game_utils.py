"""Утилиты для игр"""
from database import Database
from config import EMOJI

db = Database()

async def process_game_result(update, context, user_id: int, net_change: int, game_type: str, result_text: str):
    """Обработать результат игры и отправить сообщение"""
    db.update_balance(user_id, net_change, game_type)
    user_data = db.get_user(user_id)

    final_text = f"{result_text}\n\n💰 Новый баланс: {user_data['balance']} монет"

    from keyboards import get_back_keyboard
    await update.message.reply_text(final_text, reply_markup=get_back_keyboard())

    # Очищаем данные игры
    clear_game_data(context, game_type)

def clear_game_data(context: ContextTypes.DEFAULT_TYPE, game_type: str):
    """Очистить данные игры из context"""
    if game_type == "dice":
        context.user_data.pop("dice_bet_type", None)
        context.user_data.pop("dice_number", None)
    elif game_type == "roulette":
        context.user_data.pop("roulette_bet_type", None)
        context.user_data.pop("roulette_bet_value", None)
    else:
        context.user_data.pop("current_game", None)