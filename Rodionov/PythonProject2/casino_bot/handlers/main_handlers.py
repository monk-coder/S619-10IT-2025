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

        # Обработчик текстовых сообщений из меню
        @self.bot.message_handler(func=lambda message: True, content_types=['text'])
        def handle_all_messages(message):
            self.handle_text_messages(message)

    # ==================== ОБНОВЛЕННЫЕ ОСНОВНЫЕ ФУНКЦИИ ====================

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

    def handle_text_messages(self, message):
        """Обработчик текстовых сообщений из меню - ИСПРАВЛЕННЫЙ"""
        user_id = message.from_user.id

        # Пропускаем команды
        if message.text.startswith('/'):
            return

        # Проверяем, не ожидает ли бот ввод от пользователя для игр
        if hasattr(self.bot, 'game_handlers'):
            game_handlers = self.bot.game_handlers
            if (game_handlers.is_waiting_for_bet(user_id) or
                    game_handlers.is_waiting_for_roulette_number(message.chat.id)):
                return

        try:
            # Обработка кнопок меню
            if message.text == '💰 Баланс':
                self.handle_balance(message)

            elif message.text == '📊 Статистика':
                self.handle_stats(message)

            elif message.text == 'ℹ️ Помощь':
                self.handle_help(message)

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

    # ... остальные методы (handle_stats, handle_help, handle_daily_bonus и т.д.) остаются без изменений
    # Они должны быть скопированы из вашего текущего файла

    def handle_stats(self, message):
        """Обработчик команды /stats"""
        user_id = message.from_user.id
        try:
            stats = self.transaction_manager.get_user_stats(user_id)
            balance = self.db.get_user_balance(user_id)
            # ... остальная реализация
        except Exception as e:
            logger.error(f"Ошибка в handle_stats: {e}")

    def handle_help(self, message):
        """Обработчик команды /help"""
        try:
            help_text = """
🎰 *ПОМОЩЬ ПО КАЗИНО БОТУ* 🎰
// ... остальной текст помощи
"""
            self.safe_send_message(message.chat.id, help_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Ошибка в handle_help: {e}")

    def handle_daily_bonus(self, message):
        """Обработчик ежедневного бонуса"""
        user_id = message.from_user.id
        try:
            # ... реализация выдачи бонуса
            pass
        except Exception as e:
            logger.error(f"Ошибка в handle_daily_bonus: {e}")

    def get_daily_bonus_info(self, user_id: int) -> str:
        """Получить информацию о статусе бонуса"""
        # ... реализация проверки бонуса
        return "🎁 Бонус доступен!"

    def handle_top_players(self, message):
        """Показать топ игроков"""
        try:
            # ... реализация топа
            pass
        except Exception as e:
            logger.error(f"Ошибка в handle_top_players: {e}")

    def handle_profile(self, message):
        """Показать профиль пользователя"""
        user_id = message.from_user.id
        try:
            # ... реализация профиля
            pass
        except Exception as e:
            logger.error(f"Ошибка в handle_profile: {e}")

    def handle_myid(self, message):
        """Показать ID пользователя"""
        try:
            user_id = message.from_user.id
            # ... реализация
        except Exception as e:
            logger.error(f"Ошибка в handle_myid: {e}")