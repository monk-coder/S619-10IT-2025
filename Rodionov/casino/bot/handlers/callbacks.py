from telegram import Update
from telegram.ext import ContextTypes
from bot.utils.keyboards import main_menu_keyboard, slots_keyboard, coin_flip_keyboard


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_main":
        keyboard = main_menu_keyboard()
        await query.edit_message_text("🎰 Главное меню:", reply_markup=keyboard)

    elif data == "game_slots":
        keyboard = slots_keyboard()
        await query.edit_message_text(
            "🎰 Игровые автоматы\n\nВыберите действие:",
            reply_markup=keyboard
        )

    elif data == "game_coin":
        keyboard = coin_flip_keyboard()
        await query.edit_message_text(
            "🪙 Подбросить монетку\n\nВыберите сторону:",
            reply_markup=keyboard
        )

    elif data == "balance":
        from bot.handlers.balance import balance_handler
        # Здесь нужно передать баланс через контекст или БД
        await query.edit_message_text("💰 Загрузка баланса...")

    elif data.startswith("coin_"):
        choice = data.split("_")[1]
        # Обработка выбора монетки
        await query.edit_message_text(f"🪙 Вы выбрали: {choice}\n\nВведите ставку: /coin {choice} <ставка>")