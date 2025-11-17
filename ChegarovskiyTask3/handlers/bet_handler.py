"""Обработчики всех текстовых сообщений"""
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from games.slots import SlotMachine
from games.blackjack import Blackjack
from games.dice import DiceGame
from games.roulette import Roulette
from keyboards import get_back_keyboard

db = Database()


class InputValidator:
    """Класс для валидации ввода"""

    @staticmethod
    async def validate_number_input(update: Update, text: str) -> int:
        """Проверить и преобразовать числовой ввод"""
        try:
            return int(text)
        except ValueError:
            await update.message.reply_text("❌ Введите целое число!")
            return None

    @staticmethod
    async def validate_bet_amount(update: Update, user_balance: int, bet_amount: int) -> bool:
        """Проверить валидность ставки"""
        if bet_amount <= 0:
            await update.message.reply_text("❌ Ставка должна быть положительным числом!")
            return False
        if bet_amount > user_balance:
            await update.message.reply_text("❌ Недостаточно средств на балансе!")
            return False
        return True


class GameResultFormatter:
    """Класс для форматирования результатов игр"""

    @staticmethod
    def format_dice_result(bet_amount: int, bet_type: str, number: int, dice1: int, dice2: int, total: int, win_amount: int) -> str:
        """Форматировать результат игры в кости"""
        bet_descriptions = {
            "number": f"число {number}",
            "even": "чёт",
            "odd": "нечёт",
            "double": "дубль"
        }

        bet_description = bet_descriptions.get(bet_type, "неизвестная ставка")
        result_emoji = "🎉" if win_amount > 0 else "😞"
        result_text = "Поздравляем с выигрышем!" if win_amount > 0 else "Повезёт в следующий раз!"

        return (
            f"🎲 **КОСТИ** | Ставка: {bet_amount} на {bet_description}\n\n"
            f"Результат: {dice1} + {dice2} = {total}\n"
            f"Выигрыш: {win_amount} монет\n\n"
            f"{result_emoji} {result_text}"
        )

    @staticmethod
    def format_roulette_result(bet_amount: int, bet_type: str, bet_value: int, winning_number: int, win_amount: int) -> str:
        """Форматировать результат игры в рулетку"""
        bet_descriptions = {
            "number": f"число {bet_value}",
            "color": f"{'красное' if bet_value == 'red' else 'чёрное'}",
            "even_odd": f"{'чёт' if bet_value == 'even' else 'нечёт'}"
        }

        color_emoji = "🟢" if winning_number == 0 else "🔴" if winning_number in Roulette.RED_NUMBERS else "⚫"
        bet_description = bet_descriptions.get(bet_type, "неизвестная ставка")
        result_emoji = "🎉" if win_amount > 0 else "😞"
        result_text = "Поздравляем с выигрышем!" if win_amount > 0 else "Повезёт в следующий раз!"

        return (
            f"🎡 **РУЛЕТКА** | Ставка: {bet_amount} на {bet_description}\n\n"
            f"Выпало: {winning_number} {color_emoji}\n"
            f"Выигрыш: {win_amount} монет\n\n"
            f"{result_emoji} {result_text}"
        )

    @staticmethod
    def format_slots_result(reels: list, bet_amount: int, win_amount: int, multiplier: int) -> str:
        """Форматировать результат игры в слоты"""
        reels_display = " ".join(f"[{symbol}]" for symbol in reels)

        if multiplier == 5:
            result_text = "🎉 ДЖЕКПОТ! 3 одинаковых символа!"
        elif multiplier == 2:
            result_text = "👍 Хорошо! 2 одинаковых символа!"
        else:
            result_text = "😞 Повезёт в следующий раз!"

        return (
            f"🎰 **СЛОТ-МАШИНА**\n\n"
            f"Результат: {reels_display}\n"
            f"Ставка: {bet_amount} монет\n"
            f"Выигрыш: {win_amount} монет\n"
            f"**{result_text}**"
        )


class GameProcessor:
    """Класс для обработки игровых процессов"""

    def __init__(self):
        self.validator = InputValidator()
        self.formatter = GameResultFormatter()

    async def process_game_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                               net_change: int, game_type: str, result_text: str):
        """Обработать результат игры и отправить сообщение"""
        db.update_balance(user_id, net_change, game_type)
        user_data = db.get_user(user_id)

        final_text = f"{result_text}\n\n💰 Новый баланс: {user_data['balance']} монет"
        await update.message.reply_text(final_text, reply_markup=get_back_keyboard())
        self._clear_game_data(context, game_type)

    def _clear_game_data(self, context: ContextTypes.DEFAULT_TYPE, game_type: str):
        """Очистить данные игры из context"""
        game_data_map = {
            "dice": ["dice_bet_type", "dice_number"],
            "roulette": ["roulette_bet_type", "roulette_bet_value"],
            "slots": ["current_game"],
            "blackjack": ["current_game"]
        }

        for key in game_data_map.get(game_type, []):
            context.user_data.pop(key, None)


# Создаем экземпляр процессора
game_processor = GameProcessor()


async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать ВСЕ текстовые сообщения"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if not user_data:
        await update.message.reply_text("❌ Сначала используйте /start")
        return

    # Проверяем числовой ввод
    number = await game_processor.validator.validate_number_input(update, update.message.text)
    if number is None:
        return

    # Определяем тип игры и обрабатываем
    if "dice_bet_type" in context.user_data:
        await _handle_dice_game(update, context, user.id, number, user_data['balance'])
    elif "roulette_bet_type" in context.user_data:
        await _handle_roulette_game(update, context, user.id, number, user_data['balance'])
    elif context.user_data.get("current_game") == "slots":
        await _handle_slots_game(update, context, user.id, number, user_data['balance'])
    elif context.user_data.get("current_game") == "blackjack":
        await _start_blackjack_game(update, context, user.id, number, user_data['balance'])
    else:
        await update.message.reply_text("❌ Сначала выберите игру!")


async def _handle_dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, number: int, user_balance: int) -> None:
    """Обработать игру в кости"""
    bet_type = context.user_data["dice_bet_type"]

    # Если нужно ввести конкретное число
    if bet_type == "number" and "dice_number" not in context.user_data:
        if not (2 <= number <= 12):
            await update.message.reply_text("❌ Число должно быть от 2 до 12!")
            return
        context.user_data["dice_number"] = number
        await update.message.reply_text(
            f"🎲 **КОСТИ** | Ставка на число {number}\n\nВведите сумму ставки:",
            reply_markup=get_back_keyboard()
        )
        return

    # Обрабатываем ставку
    if not await game_processor.validator.validate_bet_amount(update, user_balance, number):
        return

    dice_number = context.user_data.get("dice_number")
    dice1, dice2, total, win_amount = DiceGame.roll(number, bet_type, dice_number)
    net_change = win_amount - number

    result_text = game_processor.formatter.format_dice_result(
        number, bet_type, dice_number, dice1, dice2, total, win_amount
    )

    await game_processor.process_game_result(update, context, user_id, net_change, "dice", result_text)


async def _handle_roulette_game(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, number: int, user_balance: int) -> None:
    """Обработать игру в рулетку"""
    bet_type = context.user_data["roulette_bet_type"]

    # Если нужно ввести конкретное число
    if bet_type == "number" and "roulette_bet_value" not in context.user_data:
        if not (0 <= number <= 36):
            await update.message.reply_text("❌ Число должно быть от 0 до 36!")
            return
        context.user_data["roulette_bet_value"] = number
        await update.message.reply_text(
            f"🎡 **РУЛЕТКА** | Ставка на число {number}\n\nВведите сумму ставки:",
            reply_markup=get_back_keyboard()
        )
        return

    # Обрабатываем ставку
    if not await game_processor.validator.validate_bet_amount(update, user_balance, number):
        return

    bet_value = context.user_data.get("roulette_bet_value")
    winning_number = Roulette.spin()
    win_amount = Roulette.calculate_payout(bet_type, bet_value, winning_number) * number
    net_change = win_amount - number

    result_text = game_processor.formatter.format_roulette_result(
        number, bet_type, bet_value, winning_number, win_amount
    )

    await game_processor.process_game_result(update, context, user_id, net_change, "roulette", result_text)


async def _handle_slots_game(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bet_amount: int, user_balance: int) -> None:
    """Играть в слоты"""
    if not await game_processor.validator.validate_bet_amount(update, user_balance, bet_amount):
        return

    reels, multiplier = SlotMachine.spin()
    win_amount = bet_amount * multiplier if multiplier > 0 else 0
    net_change = win_amount - bet_amount

    result_text = game_processor.formatter.format_slots_result(reels, bet_amount, win_amount, multiplier)
    await game_processor.process_game_result(update, context, user_id, net_change, "slots", result_text)


async def _start_blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, bet: int, user_balance: int) -> None:
    """Начать игру в блекджек"""
    if not await game_processor.validator.validate_bet_amount(update, user_balance, bet):
        return

    game = Blackjack()
    player_hand = [game.deal_card(), game.deal_card()]
    dealer_hand = [game.deal_card(), game.deal_card()]

    context.user_data["blackjack"] = {
        "game": game,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "bet": bet,
        "user_id": user_id
    }

    await _show_blackjack_state(update, context, "Ваш ход:")


async def _show_blackjack_state(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = "") -> None:
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

    from handlers.callback_handler import get_blackjack_keyboard

    if update.callback_query:
        await update.callback_query.edit_message_text(state_text, reply_markup=get_blackjack_keyboard())
    else:
        await update.message.reply_text(state_text, reply_markup=get_blackjack_keyboard())