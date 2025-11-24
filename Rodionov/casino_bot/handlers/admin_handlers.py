# handlers/admin_handlers.py
import telebot
import logging
from telebot import types
from config.config import Config
from database.db_handler import DatabaseHandler

logger = logging.getLogger(__name__)


class AdminHandlers:
    def __init__(self, bot: telebot.TeleBot, db_handler: DatabaseHandler):
        self.bot = bot
        self.db = db_handler
        self.user_states = {}

        self.register_handlers()

    def set_bot_running(self, running: bool):
        """Метод для совместимости с main.py"""
        pass

    def register_handlers(self):
        """Регистрация обработчиков для администраторов"""

        @self.bot.message_handler(commands=['admin'])
        def admin_command(message):
            self.handle_admin(message)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
        def handle_admin_callback(call):
            self.handle_admin_callback(call)

        @self.bot.message_handler(func=lambda message: self.is_waiting_for_user_id(message.from_user.id))
        def handle_user_id_input(message):
            self.handle_user_id_input(message)

        @self.bot.message_handler(func=lambda message: self.is_waiting_for_amount(message.from_user.id))
        def handle_amount_input(message):
            self.handle_amount_input(message)

    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in Config.ADMIN_IDS

    def is_waiting_for_user_id(self, user_id: int) -> bool:
        """Проверяет, ожидает ли бот ID пользователя"""
        return user_id in self.user_states and 'waiting_for_user_id' in self.user_states[user_id]

    def is_waiting_for_amount(self, user_id: int) -> bool:
        """Проверяет, ожидает ли бот сумму"""
        return user_id in self.user_states and 'waiting_for_amount' in self.user_states[user_id]

    def handle_admin(self, message):
        """Обработчик админ-панели"""
        if not self.is_admin(message.from_user.id):
            self.bot.send_message(message.chat.id, "❌ Доступ запрещен")
            return

        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton('💰 Изменить баланс', callback_data='admin_balance'),
            types.InlineKeyboardButton('👥 Поиск пользователя', callback_data='admin_find_user'),
            types.InlineKeyboardButton('📊 Статистика бота', callback_data='admin_stats'),
            types.InlineKeyboardButton('🎮 Статистика игр', callback_data='admin_games')
        ]

        markup.add(buttons[0], buttons[1])
        markup.add(buttons[2], buttons[3])

        self.bot.send_message(
            message.chat.id,
            "👑 *Админ-панель* 👑\nВыберите действие:",
            reply_markup=markup,
            parse_mode='Markdown'
        )

    def handle_admin_callback(self, call):
        """Обработчик callback от админ-панели"""
        if not self.is_admin(call.from_user.id):
            self.bot.answer_callback_query(call.id, "❌ Доступ запрещен")
            return

        data_parts = call.data.split('_')
        if len(data_parts) < 2:
            return

        action = data_parts[1]

        logger.info(f"Admin callback: {call.data}, action: {action}")

        if action == 'balance':
            self.handle_change_balance(call)
        elif action == 'find':
            self.handle_find_user(call)
        elif action == 'stats':
            self.handle_admin_stats(call)
        elif action == 'games':
            self.handle_admin_games(call)
        elif action == 'balance_user':
            # Обработка прямой ссылки на изменение баланса пользователя
            if len(data_parts) >= 3:
                target_user_id = int(data_parts[2])
                self.start_balance_change_for_user(call, target_user_id)

        self.bot.answer_callback_query(call.id)

    def handle_change_balance(self, call):
        """Обработчик изменения баланса"""
        logger.info("Starting balance change process")
        self.bot.send_message(
            call.message.chat.id,
            "👤 Введите ID пользователя, которому хотите изменить баланс:"
        )
        self.user_states[call.from_user.id] = {
            'waiting_for_user_id': True,
            'action': 'change_balance'
        }

    def handle_find_user(self, call):
        """Обработчик поиска пользователя"""
        logger.info("Starting user search process")
        self.bot.send_message(
            call.message.chat.id,
            "🔍 Введите ID пользователя для поиска:"
        )
        self.user_states[call.from_user.id] = {
            'waiting_for_user_id': True,
            'action': 'find_user'
        }

    def start_balance_change_for_user(self, call, target_user_id):
        """Начать изменение баланса для конкретного пользователя"""
        self.user_states[call.from_user.id] = {
            'waiting_for_amount': True,
            'target_user_id': target_user_id,
            'action': 'change_balance'
        }

        user = self.db.get_user(target_user_id)
        username = f"@{user.username}" if user and user.username else "Неизвестно"
        first_name = user.first_name if user else "Неизвестно"

        self.bot.send_message(
            call.message.chat.id,
            f"💰 Изменение баланса для пользователя:\n"
            f"👤 {first_name} ({username})\n"
            f"🆔 ID: {target_user_id}\n\n"
            "Введите сумму для изменения баланса:\n"
            "(используйте + для добавления, - для вычитания, например: +1000 или -500)"
        )

    def handle_user_id_input(self, message):
        """Обработчик ввода ID пользователя"""
        user_id = message.from_user.id
        user_state = self.user_states.get(user_id, {})

        try:
            target_user_id = int(message.text)
            action = user_state.get('action')

            if action == 'change_balance':
                # Сохраняем ID пользователя и запрашиваем сумму
                self.user_states[user_id] = {
                    'waiting_for_amount': True,
                    'target_user_id': target_user_id,
                    'action': 'change_balance'
                }

                user = self.db.get_user(target_user_id)
                username = f"@{user.username}" if user and user.username else "Неизвестно"
                first_name = user.first_name if user else "Неизвестно"

                self.bot.send_message(
                    message.chat.id,
                    f"💰 Изменение баланса для пользователя:\n"
                    f"👤 {first_name} ({username})\n"
                    f"🆔 ID: {target_user_id}\n\n"
                    "Введите сумму для изменения баланса:\n"
                    "(используйте + для добавления, - для вычитания, например: +1000 или -500)"
                )

            elif action == 'find_user':
                # Ищем пользователя
                self.show_user_info(message, target_user_id)

        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите корректный ID пользователя (число)"
            )

    def handle_amount_input(self, message):
        """Обработчик ввода суммы"""
        user_id = message.from_user.id
        user_state = self.user_states.get(user_id, {})

        try:
            amount_str = message.text.strip()
            target_user_id = user_state.get('target_user_id')
            action = user_state.get('action')

            if action == 'change_balance':
                # Определяем знак операции
                if amount_str.startswith('+'):
                    amount = int(amount_str[1:])
                    operation = "добавление"
                    operation_symbol = "+"
                elif amount_str.startswith('-'):
                    amount = -int(amount_str[1:])
                    operation = "списание"
                    operation_symbol = "-"
                else:
                    amount = int(amount_str)
                    operation = "установка"
                    operation_symbol = "="

                # Получаем текущий баланс
                old_balance = self.db.get_user_balance(target_user_id)

                # Изменяем баланс
                success = self.db.update_user_balance(target_user_id, amount)

                if success:
                    # Получаем обновленный баланс
                    new_balance = self.db.get_user_balance(target_user_id)
                    user_info = self.db.get_user(target_user_id)

                    username = user_info.username if user_info else "Неизвестно"
                    first_name = user_info.first_name if user_info else "Неизвестно"

                    result_text = f"""
✅ *Баланс успешно изменен!*

👤 *Пользователь:* {first_name} (@{username})
🆔 *ID:* {target_user_id}
💰 *Операция:* {operation} {abs(amount)} 🪙
💎 *Было:* {old_balance} 🪙
💎 *Стало:* {new_balance} 🪙
📊 *Изменение:* {operation_symbol}{abs(amount)} 🪙
                    """

                    self.bot.send_message(
                        message.chat.id,
                        result_text,
                        parse_mode='Markdown'
                    )

                    # Логируем транзакцию
                    from database.models import Transaction
                    transaction = Transaction(
                        user_id=target_user_id,
                        type="admin_adjustment",
                        amount=amount,
                        description=f"Корректировка баланса администратором {user_id}"
                    )
                    self.db.add_transaction(transaction)

                else:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Ошибка при изменении баланса"
                    )

                # Очищаем состояние
                if user_id in self.user_states:
                    del self.user_states[user_id]

        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите корректную сумму (например: +1000, -500, 2000)"
            )

    def show_user_info(self, message, target_user_id):
        """Показать информацию о пользователе - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        user = self.db.get_user(target_user_id)

        if not user:
            self.bot.send_message(
                message.chat.id,
                f"❌ Пользователь с ID {target_user_id} не найден"
            )
            return

        # Получаем историю транзакций
        transactions = self.db.get_user_transactions(target_user_id, limit=5)
        game_history = self.db.get_user_game_history(target_user_id, limit=5)

        # ИСПРАВЛЕНО: используем правильные названия полей из модели User
        user_info = f"""
👤 *Информация о пользователе:*

🆔 *ID:* {user.user_id}
👤 *Имя:* {user.first_name or 'Не указано'}
📛 *Фамилия:* {user.last_name or 'Не указано'}
📧 *Username:* @{user.username or 'Не указано'}
💎 *Баланс:* {user.balance} 🪙
📅 *Регистрация:* {user.created_at or 'Неизвестно'}
🕐 *Активность:* {user.last_activity or 'Неизвестно'}

🎮 *Последние игры:* {len(game_history)}
💳 *Последние транзакции:* {len(transactions)}
        """

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('💰 Изменить баланс', callback_data=f'admin_balance_user_{target_user_id}'))

        self.bot.send_message(
            message.chat.id,
            user_info,
            reply_markup=markup,
            parse_mode='Markdown'
        )

        # Очищаем состояние
        if message.from_user.id in self.user_states:
            del self.user_states[message.from_user.id]

    def handle_admin_stats(self, call):
        """Показать статистику бота"""
        try:
            stats = self.db.get_global_stats()

            stats_text = f"""
📊 *СТАТИСТИКА АДМИНИСТРАТОРА*

👥 *Всего пользователей:* {stats['total_users']}
🎮 *Всего сыграно игр:* {stats['total_games']}
💰 *Общая сумма ставок:* {stats['total_bet']} 🪙
🎯 *Общая сумма выигрышей:* {stats['total_win']} 🪙
🏦 *Прибыль казино:* {stats['casino_profit']} 🪙
👤 *Активных игроков (7 дней):* {stats['active_users']}

*Распределение по играм:*
"""

            # Добавляем детальную статистику по играм
            game_stats = self.db.get_game_stats()
            for game_type, stats_data in game_stats.items():
                game_name = {
                    'slots': '🎰 Слоты',
                    'dice': '🎯 Кости',
                    'roulette': '🎡 Рулетка'
                }.get(game_type, game_type)

                profit = stats_data['profit']
                profit_emoji = "📈" if profit > 0 else "📉" if profit < 0 else "➖"

                stats_text += f"\n{game_name}: {stats_data['games']} игр ({profit_emoji} {profit} 🪙)"

            # Добавляем топ игроков
            top_players = self.db.get_top_players_global(limit=5)
            if top_players:
                stats_text += "\n\n🏆 *Топ-5 игроков:*"
                for i, player in enumerate(top_players, 1):
                    username = f"@{player['username']}" if player['username'] else player['first_name'] or "Аноним"
                    stats_text += f"\n{i}. {username} - {player['balance']} 🪙"

            try:
                self.bot.edit_message_text(
                    stats_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown',
                    reply_markup=call.message.reply_markup
                )
            except:
                self.bot.send_message(
                    call.message.chat.id,
                    stats_text,
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            self.bot.send_message(
                call.message.chat.id,
                "❌ Ошибка при получении статистики"
            )

    def handle_admin_games(self, call):
        """Показать статистику игр"""
        try:
            game_stats = self.db.get_game_stats()

            games_text = "🎮 *Статистика по играм:*\n\n"

            for game_type, stats in game_stats.items():
                game_name = {
                    'slots': '🎰 Слоты',
                    'dice': '🎯 Кости',
                    'roulette': '🎡 Рулетка'
                }.get(game_type, game_type)

                games_text += f"""*{game_name}:*
• Игр: {stats['games']}
• Ставок: {stats['total_bet']} 🪙
• Выигрышей: {stats['total_win']} 🪙
• Прибыль: {stats['profit']} 🪙

"""

            try:
                self.bot.edit_message_text(
                    games_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown',
                    reply_markup=call.message.reply_markup
                )
            except:
                # Если не удалось редактировать, отправляем новое сообщение
                self.bot.send_message(
                    call.message.chat.id,
                    games_text,
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Ошибка при получении статистики игр: {e}")
            self.bot.send_message(
                call.message.chat.id,
                "❌ Ошибка при получении статистики игр"
            )