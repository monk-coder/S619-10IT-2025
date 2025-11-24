# handlers/main_handlers.py
import telebot
import logging
import random
import time
from telebot import types
from datetime import datetime, timedelta
from config.config import Config
from database.db_handler import DatabaseHandler
from keyboards.main_menu import get_main_menu, get_back_to_menu_keyboard
from utils.helpers import format_balance, get_time_based_greeting
from utils.transactions import TransactionManager

logger = logging.getLogger(__name__)


class MainHandlers:
    def __init__(self, bot: telebot.TeleBot, db_handler: DatabaseHandler):
        self.bot = bot
        self.db = db_handler
        self.transaction_manager = TransactionManager(db_handler)
        self.user_cooldowns = {}
        self.user_sessions = {}

        self.register_handlers()

    def safe_send_message(self, chat_id, text, **kwargs):
        """Безопасная отправка сообщения с обработкой ошибок"""
        try:
            return self.bot.send_message(chat_id, text, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в {chat_id}: {e}")
            return None

    def register_handlers(self):
        """Регистрация обработчиков"""

        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            self.handle_start(message)

        @self.bot.message_handler(commands=['balance'])
        def balance_command(message):
            self.handle_balance(message)

        @self.bot.message_handler(commands=['stats'])
        def stats_command(message):
            self.handle_stats(message)

        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            self.handle_help(message)

        @self.bot.message_handler(commands=['myid'])
        def myid_command(message):
            self.handle_myid(message)

        @self.bot.message_handler(commands=['daily', 'bonus'])
        def daily_bonus_command(message):
            self.handle_daily_bonus(message)

        @self.bot.message_handler(commands=['top'])
        def top_players_command(message):
            self.handle_top_players(message)

        @self.bot.message_handler(commands=['profile', 'me'])
        def profile_command(message):
            self.handle_profile(message)

        @self.bot.message_handler(commands=['global_stats', 'global'])
        def global_stats_command(message):
            self.handle_global_stats(message)

        # Обработчик текстовых сообщений из меню
        @self.bot.message_handler(func=lambda message: True, content_types=['text'])
        def handle_all_messages(message):
            self.handle_text_messages(message)

    def handle_start(self, message):
        """Обработчик команды /start"""
        user_id = message.from_user.id

        try:
            user = self.db.create_user(
                user_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )

            balance = self.db.get_user_balance(user_id)
            if balance is None:
                balance = 1000

            bonus_info = self.get_daily_bonus_info(user_id)
            greeting = get_time_based_greeting()

            welcome_text = f"""
{greeting}, {message.from_user.first_name}! 👋

🎰 *Добро пожаловать в Казино Бот!* 🎰

💰 *Ваш стартовый баланс:* {format_balance(balance)}

{bonus_info}

🎮 Выберите игру из меню ниже и удачи! 🍀
            """

            self.safe_send_message(
                message.chat.id,
                welcome_text,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Ошибка в handle_start для пользователя {user_id}: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при запуске. Попробуйте снова.",
                reply_markup=get_main_menu()
            )

    def handle_balance(self, message):
        """Обработчик команды /balance"""
        user_id = message.from_user.id

        try:
            balance = self.db.get_user_balance(user_id)
            bonus_info = self.get_daily_bonus_info(user_id)

            balance_text = f"""
💰 *ВАШ БАЛАНС:* {format_balance(balance)}

{bonus_info}

🎮 Для игры выберите вариант из меню ниже
            """

            self.safe_send_message(
                message.chat.id,
                balance_text,
                reply_markup=get_main_menu(),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка в handle_balance для пользователя {user_id}: {e}")
            self.safe_send_message(
                message.chat.id,
                "❌ Ошибка при получении баланса. Попробуйте позже.",
                reply_markup=get_main_menu()
            )

    # handlers/main_handlers.py (исправленная часть handle_text_messages)
    def handle_text_messages(self, message):
        """Обработчик текстовых сообщений из меню"""
        user_id = message.from_user.id

        # Пропускаем команды
        if message.text.startswith('/'):
            return

        # Проверяем, не ожидает ли бот ввод от пользователя для игр
        if hasattr(self.bot, 'game_handlers'):
            game_handlers = self.bot.game_handlers
            if (hasattr(game_handlers, 'is_waiting_for_bet') and game_handlers.is_waiting_for_bet(user_id)):
                return
            if (hasattr(game_handlers, 'is_waiting_for_roulette_number') and
                    game_handlers.is_waiting_for_roulette_number(message.chat.id)):
                return

        try:
            # Обработка кнопок меню
            if message.text == '💰 Баланс':
                self.handle_balance(message)

            elif message.text == '📊 Статистика':
                self.handle_stats(message)

            elif message.text == '🌍 Глобальная статистика':
                self.handle_global_stats(message)

            elif message.text == 'ℹ️ Помощь':
                self.handle_help(message)  # ДОБАВЛЕНО: обработка кнопки помощи

            elif message.text == '🎁 Ежедневный бонус':
                self.handle_daily_bonus(message)

            elif message.text == '🏆 Топ игроков':
                self.handle_top_players(message)

            elif message.text == '👤 Профиль':
                self.handle_profile(message)

            elif message.text in ['🎰 Слоты', '🎯 Кости', '🎡 Рулетка']:
                game_map = {
                    '🎰 Слоты': 'slots',
                    '🎯 Кости': 'dice',
                    '🎡 Рулетка': 'roulette'
                }

                game_type = game_map[message.text]
                self.show_bet_selection(message, game_type)

            else:
                self.safe_send_message(
                    message.chat.id,
                    "🎮 Используйте меню ниже для навигации по играм и функциям бота",
                    reply_markup=get_main_menu()
                )
        except Exception as e:
            logger.error(f"Ошибка в handle_text_messages: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка. Попробуйте снова.",
                reply_markup=get_main_menu()
            )
    def show_bet_selection(self, message, game_type):
        """Показать выбор ставки для игры"""
        from keyboards.game_keyboards import get_bet_keyboard

        try:
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

💰 *Ваш баланс:* {format_balance(balance)}

💎 *Выберите сумму ставки:*
            """

            self.safe_send_message(
                message.chat.id,
                bet_text,
                reply_markup=get_bet_keyboard(game_type),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка в show_bet_selection: {e}")
            self.safe_send_message(
                message.chat.id,
                "❌ Ошибка при выборе игры. Попробуйте снова.",
                reply_markup=get_main_menu()
            )

    def handle_stats(self, message):
        """Обработчик команды /stats"""
        user_id = message.from_user.id
        try:
            user = self.db.get_user(user_id)
            if not user:
                self.db.create_user(user_id)
                user = self.db.get_user(user_id)

            game_stats = self.db.get_game_stats(user_id)
            total_games = sum(stats['games'] for stats in game_stats.values())
            total_bet = sum(stats['total_bet'] for stats in game_stats.values())
            total_win = sum(stats['total_win'] for stats in game_stats.values())
            total_profit = total_win - total_bet

            stats_text = f"""
📊 *Ваша статистика:*

👤 *Игрок:* {user.first_name or 'Аноним'}
💎 *Баланс:* {format_balance(user.balance)}
🎮 *Всего игр:* {total_games}
💰 *Всего поставлено:* {total_bet} 🪙
🎯 *Всего выиграно:* {total_win} 🪙
📈 *Общий результат:* {total_profit} 🪙

*По играм:*
"""

            for game_type, stats in game_stats.items():
                game_name = {
                    'slots': '🎰 Слоты',
                    'dice': '🎯 Кости',
                    'roulette': '🎡 Рулетка'
                }.get(game_type, game_type)

                profit = stats['profit']
                profit_emoji = "📈" if profit > 0 else "📉" if profit < 0 else "➖"

                stats_text += f"\n{game_name}: {stats['games']} игр ({profit_emoji} {profit} 🪙)"

            self.safe_send_message(
                message.chat.id,
                stats_text,
                parse_mode='Markdown',
                reply_markup=get_back_to_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"Ошибка в handle_stats: {e}")
            self.safe_send_message(
                message.chat.id,
                "❌ Ошибка при получении статистики. Попробуйте позже.",
                reply_markup=get_main_menu()
            )

    def handle_global_stats(self, message):
        """Обработчик глобальной статистики"""
        try:
            stats = self.db.get_global_stats()

            stats_text = f"""
🌍 *ГЛОБАЛЬНАЯ СТАТИСТИКА БОТА*

👥 *Всего пользователей:* {stats['total_users']}
🎮 *Всего сыграно игр:* {stats['total_games']}
💰 *Общая сумма ставок:* {format_balance(stats['total_bet'])}
🎯 *Общая сумма выигрышей:* {format_balance(stats['total_win'])}
🏦 *Прибыль казино:* {format_balance(stats['casino_profit'])}
👤 *Активных игроков (7 дней):* {stats['active_users']}

*Популярные игры:*
"""

            # Добавляем популярные игры
            for game_type, count in stats['popular_games']:
                game_name = {
                    'slots': '🎰 Слоты',
                    'dice': '🎯 Кости',
                    'roulette': '🎡 Рулетка'
                }.get(game_type, game_type)

                stats_text += f"\n{game_name}: {count} игр"

            # Добавляем топ богатых игроков
            rich_players = self.db.get_rich_players(limit=5)
            if rich_players:
                stats_text += "\n\n💰 *Топ-5 богатых игроков:*"
                for i, player in enumerate(rich_players, 1):
                    username = f"@{player['username']}" if player['username'] else player['first_name'] or "Аноним"
                    stats_text += f"\n{i}. {username} - {format_balance(player['balance'])}"

            self.safe_send_message(
                message.chat.id,
                stats_text,
                parse_mode='Markdown',
                reply_markup=get_back_to_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"Ошибка в handle_global_stats: {e}")
            self.safe_send_message(
                message.chat.id,
                "❌ Ошибка при получении глобальной статистики.",
                reply_markup=get_main_menu()
            )

    # handlers/main_handlers.py (исправленный метод handle_help)
    # handlers/main_handlers.py (ИСПРАВЛЕННЫЙ handle_help)
    def handle_help(self, message):
        """Обработчик команды /help и кнопки Помощь"""
        try:
            help_text = """
    🎰 <b>ПОМОЩЬ ПО КАЗИНО БОТУ</b> 🎰

    <b>Основные команды:</b>
    /start - Запустить бота
    /balance - Проверить баланс  
    /stats - Ваша статистика
    /global_stats - Глобальная статистика
    /profile - Ваш профиль
    /top - Топ игроков
    /help - Эта справка

    <b>Игры:</b>
    🎰 Слоты - Классические игровые автоматы
    🎯 Кости - Бросок костей против бота  
    🎡 Рулетка - Европейская рулетка

    <b>Админ-команды:</b>
    /admin - Панель администратора

    <b>Как играть:</b>
    1. Выберите игру из меню
    2. Выберите сумму ставки
    3. Следуйте инструкциям игры
    4. Получайте выигрыши!

    💰 <b>Начальный баланс:</b> 1000 🪙
    🎁 <b>Ежедневный бонус:</b> Доступен раз в 24 часа

    <b>Удачи!</b> 🍀
            """

            self.safe_send_message(
                message.chat.id,
                help_text,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка в handle_help: {e}")
            # Пробуем отправить без форматирования
            try:
                help_text_simple = """
    🎰 ПОМОЩЬ ПО КАЗИНО БОТУ 🎰

    Основные команды:
    /start - Запустить бота
    /balance - Проверить баланс  
    /stats - Ваша статистика
    /global_stats - Глобальная статистика
    /profile - Ваш профиль
    /top - Топ игроков
    /help - Эта справка

    Игры:
    🎰 Слоты - Классические игровые автоматы
    🎯 Кости - Бросок костей против бота  
    🎡 Рулетка - Европейская рулетка

    Админ-команды:
    /admin - Панель администратора

    Как играть:
    1. Выберите игру из меню
    2. Выберите сумму ставки
    3. Следуйте инструкциям игры
    4. Получайте выигрыши!

    💰 Начальный баланс: 1000 🪙
    🎁 Ежедневный бонус: Доступен раз в 24 часа

    Удачи! 🍀
                """
                self.safe_send_message(
                    message.chat.id,
                    help_text_simple,
                    reply_markup=get_back_to_menu_keyboard()
                )
            except Exception as e2:
                logger.error(f"Критическая ошибка в handle_help: {e2}")
                self.safe_send_message(
                    message.chat.id,
                    "❌ Ошибка при отображении справки.",
                    reply_markup=get_main_menu()
                )
    def handle_daily_bonus(self, message):
        """Обработчик ежедневного бонуса"""
        user_id = message.from_user.id
        try:
            current_time = time.time()
            last_bonus_time = self.user_cooldowns.get(user_id, {}).get('daily_bonus', 0)

            # Проверяем, прошло ли 24 часа
            if current_time - last_bonus_time < 24 * 60 * 60:
                time_left = 24 * 60 * 60 - (current_time - last_bonus_time)
                hours_left = int(time_left // 3600)
                minutes_left = int((time_left % 3600) // 60)

                bonus_text = f"""
❌ *Бонус еще не доступен!*

⏰ Следующий бонус через:
{hours_left}ч {minutes_left}м

💎 Возвращайтесь позже!
                """
            else:
                # Выдаем бонус
                bonus_amount = random.randint(100, 500)
                self.db.update_user_balance(user_id, bonus_amount)

                # Обновляем время получения бонуса
                if user_id not in self.user_cooldowns:
                    self.user_cooldowns[user_id] = {}
                self.user_cooldowns[user_id]['daily_bonus'] = current_time

                new_balance = self.db.get_user_balance(user_id)

                bonus_text = f"""
🎉 *БОНУС ПОЛУЧЕН!* 🎉

💰 +{bonus_amount} 🪙 добавлено на ваш счет!

💎 *Теперь у вас:* {format_balance(new_balance)}

🎮 Удачи в играх! 🍀
                """

            self.safe_send_message(
                message.chat.id,
                bonus_text,
                parse_mode='Markdown',
                reply_markup=get_back_to_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"Ошибка в handle_daily_bonus: {e}")
            self.safe_send_message(
                message.chat.id,
                "❌ Ошибка при получении бонуса. Попробуйте позже.",
                reply_markup=get_main_menu()
            )

    def get_daily_bonus_info(self, user_id: int) -> str:
        """Получить информацию о статусе бонуса"""
        try:
            current_time = time.time()
            last_bonus_time = self.user_cooldowns.get(user_id, {}).get('daily_bonus', 0)

            if current_time - last_bonus_time < 24 * 60 * 60:
                time_left = 24 * 60 * 60 - (current_time - last_bonus_time)
                hours_left = int(time_left // 3600)
                minutes_left = int((time_left % 3600) // 60)
                return f"🎁 *Бонус через:* {hours_left}ч {minutes_left}м"
            else:
                return "🎁 *Ежедневный бонус доступен!* Используйте /daily"

        except Exception as e:
            logger.error(f"Ошибка в get_daily_bonus_info: {e}")
            return "🎁 *Бонусная система*"

    def handle_top_players(self, message):
        """Показать топ игроков"""
        try:
            top_players = self.db.get_top_players_global(limit=15)

            if not top_players:
                top_text = "🏆 *Топ игроков:*\n\nПока никто не играл 😢\n\nБудьте первым в топе! 🎮"
            else:
                top_text = "🏆 *ТОП-15 ИГРОКОВ* 🏆\n\n"

                for i, player in enumerate(top_players, 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    username = f"@{player['username']}" if player['username'] else player['first_name'] or "Аноним"
                    balance = player['balance']

                    # Добавляем особые эмодзи для богатых игроков
                    wealth_emoji = ""
                    if balance >= 100000:
                        wealth_emoji = "💰"
                    elif balance >= 50000:
                        wealth_emoji = "💎"
                    elif balance >= 10000:
                        wealth_emoji = "🪙"

                    top_text += f"{medal} {username} - {format_balance(balance)} {wealth_emoji}\n"

                # Добавляем статистику пользователя в топе
                user_id = message.from_user.id
                user_position = None
                user_balance = self.db.get_user_balance(user_id)

                for i, player in enumerate(top_players, 1):
                    if player['user_id'] == user_id:
                        user_position = i
                        break

                if user_position:
                    top_text += f"\n📊 *Ваша позиция:* {user_position}"
                else:
                    # Если пользователя нет в топе, показываем сколько до топа
                    if top_players:
                        min_top_balance = top_players[-1]['balance']
                        needed = min_top_balance - user_balance + 1
                        if needed > 0:
                            top_text += f"\n📊 *До топа нужно:* +{needed} 🪙"

            self.safe_send_message(
                message.chat.id,
                top_text,
                parse_mode='Markdown',
                reply_markup=get_back_to_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"Ошибка в handle_top_players: {e}")
            self.safe_send_message(
                message.chat.id,
                "❌ Ошибка при получении топа игроков.",
                reply_markup=get_main_menu()
            )

    def handle_profile(self, message):
        """Показать профиль пользователя"""
        user_id = message.from_user.id
        try:
            user = self.db.get_user(user_id)
            if not user:
                self.db.create_user(user_id)
                user = self.db.get_user(user_id)

            game_stats = self.db.get_game_stats(user_id)
            total_games = sum(stats['games'] for stats in game_stats.values())

            # Получаем историю транзакций
            transactions = self.db.get_user_transactions(user_id, limit=5)
            game_history = self.db.get_user_game_history(user_id, limit=5)

            profile_text = f"""
👤 *ВАШ ПРОФИЛЬ*

🆔 *ID:* `{user.user_id}`
👤 *Имя:* {user.first_name or 'Не указано'}
📛 *Username:* @{user.username or 'Не указано'}
💎 *Баланс:* {format_balance(user.balance)}
🎮 *Всего игр:* {total_games}
📅 *Регистрация:* {user.created_at or 'Неизвестно'}

*Последние активности:*
"""

            # Добавляем последние игры
            if game_history:
                profile_text += "\n*🎮 Последние игры:*\n"
                for game in game_history[:3]:
                    result_emoji = "🟢" if game.win > 0 else "🔴" if game.win < 0 else "🟡"
                    profile_text += f"{result_emoji} {game.game_type}: {game.win} 🪙\n"
            else:
                profile_text += "\n🎮 Игр пока не было\n"

            self.safe_send_message(
                message.chat.id,
                profile_text,
                parse_mode='Markdown',
                reply_markup=get_back_to_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"Ошибка в handle_profile: {e}")
            self.safe_send_message(
                message.chat.id,
                "❌ Ошибка при загрузке профиля.",
                reply_markup=get_main_menu()
            )

    def handle_myid(self, message):
        """Показать ID пользователя"""
        try:
            user_id = message.from_user.id
            id_text = f"""
👤 *Ваши данные:*

🆔 *ID:* `{user_id}`
👤 *Имя:* {message.from_user.first_name or 'Не указано'}
📛 *Username:* @{message.from_user.username or 'Не указано'}

💡 *Этот ID может понадобиться для технической поддержки*
            """

            self.safe_send_message(
                message.chat.id,
                id_text,
                parse_mode='Markdown',
                reply_markup=get_back_to_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"Ошибка в handle_myid: {e}")
            self.safe_send_message(
                message.chat.id,
                f"❌ Ошибка: {e}",
                reply_markup=get_main_menu()
            )