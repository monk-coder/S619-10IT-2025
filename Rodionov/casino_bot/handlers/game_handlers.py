# handlers/game_handlers.py
import telebot
import time
import logging
from config.config import Config
from database.db_handler import DatabaseHandler
from games.slots import SlotMachine
from games.dice import DiceGame
from games.roulette import RouletteGame
from animations.slots_animation import SlotsAnimation
from animations.dice_animation import DiceAnimation
from animations.roulette_animation import RouletteAnimation
from keyboards.main_menu import get_main_menu, get_back_to_menu_keyboard
from keyboards.game_keyboards import get_bet_keyboard, get_roulette_bet_keyboard, get_quick_bet_keyboard
from utils.helpers import format_balance, validate_bet
from utils.transactions import TransactionManager

logger = logging.getLogger(__name__)


class GameHandlers:
    def __init__(self, bot: telebot.TeleBot, db_handler: DatabaseHandler):
        self.bot = bot
        self.db = db_handler
        self.transaction_manager = TransactionManager(db_handler)

        self.slots_machine = SlotMachine()
        self.dice_game = DiceGame()
        self.roulette_game = RouletteGame()

        # Анимации
        self.slots_animation = SlotsAnimation()
        self.dice_animation = DiceAnimation()
        self.roulette_animation = RouletteAnimation()

        self.user_states = {}
        self.register_handlers()

    def set_bot_running(self, running: bool):
        """Метод для совместимости с main.py"""
        pass

    def register_handlers(self):
        """Регистрация обработчиков"""

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('bet_'))
        def handle_bet(call):
            self._handle_bet_selection(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('roulette_'))
        def handle_roulette_bet(call):
            self._handle_roulette_bet(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('quick_play_'))
        def handle_quick_play(call):
            game_type = call.data.split('_')[-1]
            self.show_bet_selection(call.message, game_type)
            self.bot.answer_callback_query(call.id)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('change_bet_'))
        def handle_change_bet(call):
            self._handle_change_bet(call)

        @self.bot.callback_query_handler(func=lambda call: call.data in ['back_to_menu', 'back_to_games'])
        def handle_navigation(call):
            if call.data == 'back_to_menu':
                self.bot.send_message(call.message.chat.id, "🎮 Главное меню", reply_markup=get_main_menu())
            self.bot.answer_callback_query(call.id)

        @self.bot.message_handler(func=lambda message: self._is_waiting_for_bet(message.from_user.id))
        def handle_custom_bet(message):
            self._handle_custom_bet(message)

        @self.bot.message_handler(func=lambda message: self.is_waiting_for_roulette_number(message.chat.id))
        def handle_roulette_number(message):
            self._handle_roulette_number(message)

    def _handle_roulette_number(self, message):
        """Обработчик ввода числа для рулетки"""
        chat_id = message.chat.id
        user_id = message.from_user.id

        try:
            number = int(message.text)
            if number < 0 or number > 36:
                self.bot.send_message(chat_id, "❌ Введите число от 0 до 36")
                return

            user_state = self.user_states.get(chat_id, {})
            bet_amount = user_state.get('roulette_bet_amount', 0)

            # Очищаем состояние
            if chat_id in self.user_states:
                del self.user_states[chat_id]

            self._play_roulette(user_id, message, bet_amount, 'specific', str(number))

        except ValueError:
            self.bot.send_message(chat_id, "❌ Введите корректное число от 0 до 36")

    def _handle_bet_selection(self, call):
        """Обработчик выбора ставки"""
        user_id = call.from_user.id
        data_parts = call.data.split('_')

        if len(data_parts) < 3:
            self.bot.answer_callback_query(call.id)
            return

        game_type = data_parts[1]
        bet_value = data_parts[2]

        if bet_value == 'custom':
            self.bot.send_message(call.message.chat.id, f"💎 Введите сумму ставки для {game_type}:")
            self.user_states[user_id] = {'waiting_for_bet': game_type}
            self.bot.answer_callback_query(call.id)
            return

        try:
            bet_amount = int(bet_value)
            self._process_game(user_id, call.message, game_type, bet_amount)
        except ValueError:
            self.bot.answer_callback_query(call.id)

    def _handle_custom_bet(self, message):
        """Обработчик пользовательской ставки"""
        user_id = message.from_user.id

        try:
            bet_amount = int(message.text)
            game_type = self.user_states[user_id]['waiting_for_bet']
            del self.user_states[user_id]
            self._process_game(user_id, message, game_type, bet_amount)
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Введите корректное число!")
        except KeyError:
            self.bot.send_message(message.chat.id, "❌ Ошибка состояния")

    def _process_game(self, user_id, message, game_type: str, bet_amount: int):
        """Обработка игры"""
        balance = self.db.get_user_balance(user_id)

        is_valid, validation_msg = validate_bet(str(bet_amount), Config.MIN_BET, Config.MAX_BET, balance)

        if not is_valid:
            self.bot.send_message(message.chat.id, f"❌ {validation_msg}", reply_markup=get_back_to_menu_keyboard())
            return

        if game_type == 'slots':
            self._play_slots(user_id, message, bet_amount)
        elif game_type == 'dice':
            self._play_dice(user_id, message, bet_amount)
        elif game_type == 'roulette':
            self._show_roulette_bet_types(message, bet_amount)

    def _play_slots(self, user_id, message, bet_amount: int):
        """Игра в слоты с анимацией"""
        loading_msg = self.bot.send_message(message.chat.id, f"🎰 Подготовка слотов...\n💎 Ставка: {bet_amount} 🪙")

        # Получаем результат игры
        result = self.slots_machine.play(user_id, bet_amount)

        if not result['success']:
            self.bot.edit_message_text(f"❌ {result['error']}", message.chat.id, loading_msg.message_id)
            return

        # Показываем анимацию
        animation_frames = self.slots_animation.create_animation(result['final_result'])
        for frame in animation_frames:
            try:
                self.bot.edit_message_text(frame, message.chat.id, loading_msg.message_id, parse_mode='Markdown')
                time.sleep(0.8)
            except:
                pass

        # Обработка транзакции
        self.transaction_manager.add_game_transaction(
            user_id=user_id,
            game_type='slots',
            bet=bet_amount,
            win=result['win_amount'],
            result=result['description']
        )

        new_balance = self.db.get_user_balance(user_id)
        result_text = self._format_slots_result(result, bet_amount, new_balance)

        self.bot.edit_message_text(result_text, message.chat.id, loading_msg.message_id,
                                   reply_markup=get_quick_bet_keyboard('slots'))

    def _play_dice(self, user_id, message, bet_amount: int):
        """Игра в кости с анимацией"""
        loading_msg = self.bot.send_message(message.chat.id, f"🎲 Подготовка броска...\n💎 Ставка: {bet_amount} 🪙")

        # Получаем результат игры
        result = self.dice_game.play(user_id, bet_amount)

        if not result['success']:
            self.bot.edit_message_text(f"❌ {result['error']}", message.chat.id, loading_msg.message_id)
            return

        # Показываем анимацию
        animation_frames = self.dice_animation.create_animation(result['player_roll'], result['bot_roll'])
        for frame in animation_frames:
            try:
                self.bot.edit_message_text(frame, message.chat.id, loading_msg.message_id, parse_mode='Markdown')
                time.sleep(0.8)
            except:
                pass

        # Обработка транзакции
        self.transaction_manager.add_game_transaction(
            user_id=user_id,
            game_type='dice',
            bet=bet_amount,
            win=result['win_amount'],
            result=result['description']
        )

        new_balance = self.db.get_user_balance(user_id)
        result_text = self._format_dice_result(result, bet_amount, new_balance)

        self.bot.edit_message_text(result_text, message.chat.id, loading_msg.message_id,
                                   reply_markup=get_quick_bet_keyboard('dice'))

    def _play_roulette(self, user_id, message, bet_amount: int, bet_type: str, bet_value: str):
        """Игра в рулетку с анимацией"""
        loading_msg = self.bot.send_message(message.chat.id, f"🎡 Подготовка рулетки...\n💎 Ставка: {bet_amount} 🪙")

        # Получаем результат игры
        result = self.roulette_game.play(user_id, bet_type, bet_value, bet_amount)

        if not result['success']:
            self.bot.edit_message_text(f"❌ {result['error']}", message.chat.id, loading_msg.message_id)
            return

        winning_result = result['winning_result']

        # Показываем анимацию
        animation_frames = self.roulette_animation.create_animation(
            winning_result['number'],
            winning_result['color'],
            winning_result['color_emoji']
        )
        for frame in animation_frames:
            try:
                self.bot.edit_message_text(frame, message.chat.id, loading_msg.message_id, parse_mode='Markdown')
                time.sleep(0.8)
            except:
                pass

        # Обработка транзакции
        self.transaction_manager.add_game_transaction(
            user_id=user_id,
            game_type='roulette',
            bet=bet_amount,
            win=result['payout'],
            result=f"{bet_type}_{bet_value} -> {winning_result['number']}"
        )

        new_balance = self.db.get_user_balance(user_id)
        result_text = self._format_roulette_result(result, bet_amount, new_balance)

        self.bot.edit_message_text(result_text, message.chat.id, loading_msg.message_id,
                                   reply_markup=get_quick_bet_keyboard('roulette'))

    def _show_roulette_bet_types(self, message, bet_amount: int):
        """Показать типы ставок для рулетки"""
        self.user_states[message.chat.id] = {'roulette_bet_amount': bet_amount}

        bet_text = f"""
🎡 ВЫБОР ТИПА СТАВКИ 🎡

💰 Ваша ставка: {bet_amount} 🪙

Доступные типы ставок:
🔴 Красное/Чёрное - выигрыш x2
🟢 Зелёное (0) - выигрыш x14
🔢 Чётное/Нечётное - выигрыш x2
🎯 Конкретное число - выигрыш x36
        """

        self.bot.send_message(message.chat.id, bet_text, reply_markup=get_roulette_bet_keyboard())

    def _handle_roulette_bet(self, call):
        """Обработчик ставок в рулетке"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data_parts = call.data.split('_')

        if len(data_parts) < 2:
            self.bot.answer_callback_query(call.id)
            return

        bet_type = data_parts[1]
        user_state = self.user_states.get(chat_id, {})
        bet_amount = user_state.get('roulette_bet_amount', 0)

        if bet_type == 'specific':
            self.bot.send_message(chat_id, "🎯 Введите число от 0 до 36:")
            self.user_states[chat_id] = {
                'waiting_for_roulette_number': True,
                'roulette_bet_amount': bet_amount
            }
            self.bot.answer_callback_query(call.id)
            return

        if len(data_parts) >= 3:
            bet_value = data_parts[2]
            self._play_roulette(user_id, call.message, bet_amount, bet_type, bet_value)

        self.bot.answer_callback_query(call.id)

    def _handle_change_bet(self, call):
        """Обработчик изменения ставки"""
        try:
            user_id = call.from_user.id
            data_parts = call.data.split('_')

            if len(data_parts) >= 3:
                game_type = data_parts[2]
                balance = self.db.get_user_balance(user_id)

                game_names = {
                    'slots': '🎰 СЛОТЫ',
                    'dice': '🎯 КОСТИ',
                    'roulette': '🎡 РУЛЕТКА'
                }

                bet_text = f"""
🔄 ИЗМЕНЕНИЕ СТАВКИ

{game_names.get(game_type, 'ИГРА')}

💰 Ваш баланс: {format_balance(balance)}

💎 Выберите новую сумму ставки:
                """

                self.bot.edit_message_text(
                    bet_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown',
                    reply_markup=get_bet_keyboard(game_type)
                )

            self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Ошибка в handle_change_bet: {e}")
            self.bot.answer_callback_query(call.id, "❌ Ошибка при изменении ставки")

    def show_bet_selection(self, message, game_type):
        """Показать выбор ставки"""
        balance = self.db.get_user_balance(message.from_user.id)

        if balance is None:
            balance = 1000
            self.db.create_user(message.from_user.id)

        game_names = {
            'slots': '🎰 СЛОТЫ',
            'dice': '🎯 КОСТИ',
            'roulette': '🎡 РУЛЕТКА'
        }

        bet_text = f"""
{game_names.get(game_type, 'ИГРА')}

💰 Ваш баланс: {format_balance(balance)}

💎 Выберите сумму ставки:
        """

        self.bot.send_message(message.chat.id, bet_text, reply_markup=get_bet_keyboard(game_type))

    def _is_waiting_for_bet(self, user_id):
        """Проверка ожидания ставки"""
        return user_id in self.user_states and 'waiting_for_bet' in self.user_states[user_id]

    def is_waiting_for_bet(self, user_id: int) -> bool:
        """Проверка ожидания ставки (публичный метод)"""
        return self._is_waiting_for_bet(user_id)

    def is_waiting_for_roulette_number(self, chat_id: int) -> bool:
        """Проверка ожидания числа для рулетки"""
        return chat_id in self.user_states and 'waiting_for_roulette_number' in self.user_states[chat_id]

    # Форматирование результатов
    def _format_slots_result(self, result, bet_amount, new_balance):
        return f"""
🎰 РЕЗУЛЬТАТ СЛОТОВ 🎰

   {result['final_result'][0]} | {result['final_result'][1]} | {result['final_result'][2]}

{result['description']}

💰 Ставка: {bet_amount} 🪙
🎯 Выигрыш: {result['win_amount']} 🪙
💎 Баланс: {format_balance(new_balance)}
        """

    def _format_dice_result(self, result, bet_amount, new_balance):
        outcome = "🎉 ПОБЕДА!" if result['player_roll'] > result['bot_roll'] else "😞 ПОРАЖЕНИЕ"
        if result['player_roll'] == result['bot_roll']:
            outcome = "🤝 НИЧЬЯ"

        return f"""
🎲 РЕЗУЛЬТАТ КОСТЕЙ 🎲

Ваш бросок: {result['player_roll']}
Бросок бота: {result['bot_roll']}

{outcome}

💰 Ставка: {bet_amount} 🪙
🎯 Выигрыш: {result['win_amount']} 🪙
💎 Баланс: {format_balance(new_balance)}
        """

    def _format_roulette_result(self, result, bet_amount, new_balance):
        winning_result = result['winning_result']
        return f"""
🎡 РЕЗУЛЬТАТ РУЛЕТКИ 🎡

Выпавшее число: {winning_result['color_emoji']} {winning_result['number']}

{'🎉 СТАВКА СЫГРАЛА!' if result['is_win'] else '😞 СТАВКА НЕ СЫГРАЛА'}

💰 Ставка: {bet_amount} 🪙
🎯 Выигрыш: {result['payout']} 🪙
💎 Баланс: {format_balance(new_balance)}
        """