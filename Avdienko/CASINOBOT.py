import os
import random
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
import telebot
from telebot import types

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('casino_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CasinoBot:
    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token)
        self.db_path = 'casino_bot.db'
        self.min_bet = 10
        self.max_bet = 10000
        self.start_balance = 1000

        # Инициализация базы данных
        self.init_db()

        # Регистрация обработчиков
        self.register_handlers()

    def init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 1000,
                    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица игр
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game_type TEXT,
                    bet_amount INTEGER,
                    win_amount INTEGER,
                    result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            conn.commit()

    def get_user_balance(self, user_id: int) -> int:
        """Получение баланса пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()

            if result is None:
                # Регистрируем нового пользователя
                cursor.execute(
                    'INSERT INTO users (user_id, balance) VALUES (?, ?)',
                    (user_id, self.start_balance)
                )
                conn.commit()
                return self.start_balance

            return result[0]

    def update_user_balance(self, user_id: int, amount: int):
        """Обновление баланса пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            conn.commit()

    def save_game_result(self, user_id: int, game_type: str, bet_amount: int,
                         win_amount: int, result: str):
        """Сохранение результата игры"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO games (user_id, game_type, bet_amount, win_amount, result)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, game_type, bet_amount, win_amount, result))
            conn.commit()

    def register_handlers(self):
        """Регистрация обработчиков команд"""

        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            self.handle_start(message)

        @self.bot.message_handler(commands=['balance'])
        def balance_handler(message):
            self.handle_balance(message)

        @self.bot.message_handler(commands=['games'])
        def games_handler(message):
            self.handle_games_menu(message)

        @self.bot.message_handler(commands=['help'])
        def help_handler(message):
            self.handle_help(message)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            self.handle_callback(call)

    def handle_start(self, message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name

        balance = self.get_user_balance(user_id)

        welcome_text = f"""
🎰 Добро пожаловать в казино-бот, {username}!

💰 Ваш баланс: {balance} монет

🎮 Доступные игры:
• 🎡 Слот-машина
• 🎯 Кости
• 🔢 Угадай число

📊 Статистика и управление:
• /balance - ваш баланс
• /games - меню игр
• /help - помощь

⚠️ Играйте ответственно!
        """

        self.bot.send_message(message.chat.id, welcome_text)

    def handle_balance(self, message):
        """Обработчик команды /balance"""
        user_id = message.from_user.id
        balance = self.get_user_balance(user_id)

        self.bot.send_message(
            message.chat.id,
            f"💰 Ваш текущий баланс: {balance} монет"
        )

    def handle_help(self, message):
        """Обработчик команды /help"""
        help_text = """
🎰 *Помощь по казино-боту*

*Основные команды:*
/start - начать работу с ботом
/balance - показать баланс
/games - меню игр
/help - эта справка

*Правила игр:*

🎡 *Слот-машина*
• Ставка: 10-10000 монет
• 3 одинаковых символа = выигрыш x5
• 2 одинаковых символа = выигрыш x2

🎯 *Кости*
• Ставка: 10-10000 монет
• Бросаете 2 кости
• Сумма 7 или 11 = выигрыш x3
• Дубль = выигрыш x2
• Проигрыш в остальных случаях

🔢 *Угадай число*
• Ставка: 10-10000 монет
• Угадайте число от 1 до 10
• Выигрыш x8 при угадывании

⚠️ *Важно:*
• Играйте ответственно
• Не ставьте больше, чем можете позволить себе потерять
• Бот предназначен только для развлечения
        """

        self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

    def handle_games_menu(self, message):
        """Обработчик меню игр"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            types.InlineKeyboardButton("🎡 Слоты", callback_data="game_slots"),
            types.InlineKeyboardButton("🎯 Кости", callback_data="game_dice"),
            types.InlineKeyboardButton("🔢 Угадай число", callback_data="game_guess"),
            types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        ]

        keyboard.add(*buttons)

        self.bot.send_message(
            message.chat.id,
            "🎮 Выберите игру:",
            reply_markup=keyboard
        )

    def handle_callback(self, call):
        """Обработчик callback-запросов"""
        if call.data == "game_slots":
            self.start_slots_game(call.message)
        elif call.data == "game_dice":
            self.start_dice_game(call.message)
        elif call.data == "game_guess":
            self.start_guess_game(call.message)
        elif call.data == "balance":
            self.show_balance(call.message)
        elif call.data.startswith("bet_"):
            self.process_bet(call)

        self.bot.answer_callback_query(call.id)

    def show_balance(self, message):
        """Показать баланс"""
        user_id = message.chat.id
        balance = self.get_user_balance(user_id)
        self.bot.send_message(message.chat.id, f"💰 Баланс: {balance} монет")

    def start_slots_game(self, message):
        """Начало игры в слоты"""
        user_id = message.chat.id
        balance = self.get_user_balance(user_id)

        if balance < self.min_bet:
            self.bot.send_message(
                message.chat.id,
                f"❌ Недостаточно средств! Минимальная ставка: {self.min_bet} монет"
            )
            return

        keyboard = self.create_bet_keyboard("slots")
        self.bot.send_message(
            message.chat.id,
            f"🎡 Игра: Слот-машина\n💰 Ваш баланс: {balance} монет\n\nВыберите ставку:",
            reply_markup=keyboard
        )

    def start_dice_game(self, message):
        """Начало игры в кости"""
        user_id = message.chat.id
        balance = self.get_user_balance(user_id)

        if balance < self.min_bet:
            self.bot.send_message(
                message.chat.id,
                f"❌ Недостаточно средств! Минимальная ставка: {self.min_bet} монет"
            )
            return

        keyboard = self.create_bet_keyboard("dice")
        self.bot.send_message(
            message.chat.id,
            f"🎯 Игра: Кости\n💰 Ваш баланс: {balance} монет\n\nВыберите ставку:",
            reply_markup=keyboard
        )

    def start_guess_game(self, message):
        """Начало игры 'Угадай число'"""
        user_id = message.chat.id
        balance = self.get_user_balance(user_id)

        if balance < self.min_bet:
            self.bot.send_message(
                message.chat.id,
                f"❌ Недостаточно средств! Минимальная ставка: {self.min_bet} монет"
            )
            return

        keyboard = self.create_bet_keyboard("guess")
        self.bot.send_message(
            message.chat.id,
            f"🔢 Игра: Угадай число\n💰 Ваш баланс: {balance} монет\n\nВыберите ставку:",
            reply_markup=keyboard
        )

    def create_bet_keyboard(self, game_type: str) -> types.InlineKeyboardMarkup:
        """Создание клавиатуры для выбора ставки"""
        keyboard = types.InlineKeyboardMarkup(row_width=3)

        bets = [10, 50, 100, 500, 1000, 5000]
        buttons = []

        for bet in bets:
            buttons.append(
                types.InlineKeyboardButton(
                    f"{bet} 🪙",
                    callback_data=f"bet_{game_type}_{bet}"
                )
            )

        keyboard.add(*buttons[:3])
        keyboard.add(*buttons[3:])
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_games"))

        return keyboard

    def process_bet(self, call):
        """Обработка ставки"""
        try:
            _, game_type, bet_amount = call.data.split('_')
            bet_amount = int(bet_amount)
            user_id = call.from_user.id

            balance = self.get_user_balance(user_id)

            if bet_amount < self.min_bet or bet_amount > self.max_bet:
                self.bot.send_message(
                    call.message.chat.id,
                    f"❌ Недопустимая ставка! Допустимый диапазон: {self.min_bet}-{self.max_bet}"
                )
                return

            if bet_amount > balance:
                self.bot.send_message(
                    call.message.chat.id,
                    "❌ Недостаточно средств для этой ставки!"
                )
                return

            # Списываем ставку
            self.update_user_balance(user_id, -bet_amount)

            # Запускаем соответствующую игру
            if game_type == "slots":
                self.play_slots(call.message, user_id, bet_amount)
            elif game_type == "dice":
                self.play_dice(call.message, user_id, bet_amount)
            elif game_type == "guess":
                self.play_guess_number(call.message, user_id, bet_amount)

        except Exception as e:
            logger.error(f"Error processing bet: {e}")
            self.bot.send_message(call.message.chat.id, "❌ Произошла ошибка!")

    def play_slots(self, message, user_id: int, bet_amount: int):
        """Игра в слоты"""
        symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎"]

        # Генерируем случайные символы
        result = [random.choice(symbols) for _ in range(3)]
        slots_display = " | ".join(result)

        # Определяем выигрыш
        if result[0] == result[1] == result[2]:
            # Джекпот - 3 одинаковых символа
            win_amount = bet_amount * 5
            result_text = "🎉 ДЖЕКПОТ! x5"
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            # 2 одинаковых символа
            win_amount = bet_amount * 2
            result_text = "🎊 Выигрыш! x2"
        else:
            # Проигрыш
            win_amount = 0
            result_text = "❌ Проигрыш"

        # Обновляем баланс и сохраняем результат
        if win_amount > 0:
            self.update_user_balance(user_id, win_amount)

        self.save_game_result(user_id, "slots", bet_amount, win_amount, result_text)

        balance = self.get_user_balance(user_id)

        # Отправляем результат
        result_message = f"""
🎡 *СЛОТ-МАШИНА*

{slots_display}

*Результат:* {result_text}
*Ставка:* {bet_amount} 🪙
*Выигрыш:* {win_amount} 🪙
*Баланс:* {balance} 🪙
        """

        self.bot.send_message(message.chat.id, result_message, parse_mode='Markdown')

    def play_dice(self, message, user_id: int, bet_amount: int):
        """Игра в кости"""
        # Бросаем 2 кости
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2

        # Определяем выигрыш
        if total in [7, 11]:
            win_amount = bet_amount * 3
            result_text = "🎉 Большой выигрыш! x3"
        elif dice1 == dice2:
            win_amount = bet_amount * 2
            result_text = "🎊 Дубль! x2"
        else:
            win_amount = 0
            result_text = "❌ Проигрыш"

        # Обновляем баланс и сохраняем результат
        if win_amount > 0:
            self.update_user_balance(user_id, win_amount)

        self.save_game_result(user_id, "dice", bet_amount, win_amount, result_text)

        balance = self.get_user_balance(user_id)

        # Отправляем результат
        result_message = f"""
🎯 *КОСТИ*

🎲 Кость 1: {dice1}
🎲 Кость 2: {dice2}
📊 Сумма: {total}

*Результат:* {result_text}
*Ставка:* {bet_amount} 🪙
*Выигрыш:* {win_amount} 🪙
*Баланс:* {balance} 🪙
        """

        self.bot.send_message(message.chat.id, result_message, parse_mode='Markdown')

    def play_guess_number(self, message, user_id: int, bet_amount: int):
        """Игра 'Угадай число'"""
        # Генерируем случайное число
        secret_number = random.randint(1, 10)

        # Создаем клавиатуру для выбора числа
        keyboard = types.InlineKeyboardMarkup(row_width=5)
        buttons = []

        for i in range(1, 11):
            buttons.append(
                types.InlineKeyboardButton(str(i), callback_data=f"guess_{secret_number}_{i}_{bet_amount}")
            )

        # Разбиваем кнопки на строки по 5 штук
        for i in range(0, 10, 5):
            keyboard.add(*buttons[i:i + 5])

        self.bot.send_message(
            message.chat.id,
            f"🔢 Угадай число от 1 до 10!\n💰 Ставка: {bet_amount} 🪙\n\nВыберите число:",
            reply_markup=keyboard
        )

    def handle_guess(self, call):
        """Обработка угадывания числа"""
        try:
            _, secret, guess, bet = call.data.split('_')
            secret_number = int(secret)
            guessed_number = int(guess)
            bet_amount = int(bet)
            user_id = call.from_user.id

            if guessed_number == secret_number:
                win_amount = bet_amount * 8
                result_text = "🎉 Победа! x8"
                self.update_user_balance(user_id, win_amount)
            else:
                win_amount = 0
                result_text = f"❌ Проигрыш! Загадано: {secret_number}"

            self.save_game_result(user_id, "guess_number", bet_amount, win_amount, result_text)
            balance = self.get_user_balance(user_id)

            result_message = f"""
🔢 *УГАДАЙ ЧИСЛO*

Ваш выбор: {guessed_number}
Загаданное число: {secret_number}

*Результат:* {result_text}
*Ставка:* {bet_amount} 🪙
*Выигрыш:* {win_amount} 🪙
*Баланс:* {balance} 🪙
            """

            self.bot.edit_message_text(
                result_message,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error handling guess: {e}")

    def run(self):
        """Запуск бота"""
        logger.info("Casino bot started")
        self.bot.infinity_polling()


# Добавляем обработчик для угадывания чисел
def setup_guess_handler(bot_instance):
    @bot_instance.bot.callback_query_handler(func=lambda call: call.data.startswith('guess_'))
    def guess_handler(call):
        bot_instance.handle_guess(call)


if __name__ == "__main__":
    # Получаем токен из переменной окружения
    BOT_TOKEN = os.getenv('CASINO_BOT_TOKEN')

    if not BOT_TOKEN:
        print("Ошибка: Укажите токен бота в переменной окружения CASINO_BOT_TOKEN")
        exit(1)

    # Создаем и запускаем бота
    casino_bot = CasinoBot(BOT_TOKEN)
    setup_guess_handler(casino_bot)
    casino_bot.run()