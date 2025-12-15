"""
Модуль работы с базой данных
Управление пользователями, транзакциями и бонусами
"""
import sqlite3
import logging
import random
import time
from contextlib import contextmanager
from config import DATABASE_NAME, STARTING_BALANCE, REFERRAL_BONUS

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с SQLite базой данных"""

    def __init__(self, db_name: str = DATABASE_NAME):
        self.db_name = db_name
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для соединения с БД с блокировкой"""
        conn = sqlite3.connect(self.db_name, timeout=30.0)  # Таймаут 30 секунд
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Разрешаем одновременные чтения
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Инициализация таблиц базы данных"""
        with self._get_connection() as conn:
            # Создание таблицы пользователей
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 1000,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    last_bonus_time REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    games_played INTEGER DEFAULT 0
                )
            """)

            # Создание таблицы транзакций
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    amount INTEGER,
                    game_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

    def get_user(self, user_id: int):
        """Получить данные пользователя по ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()

    def create_user(self, user_id: int, username: str, referred_by: int = None):
        """Создать нового пользователя"""
        with self._get_connection() as conn:
            referral_code = f"ref_{user_id}_{random.randint(1000, 9999)}"

            conn.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, referral_code, referred_by, balance) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, username, referral_code, referred_by, STARTING_BALANCE)
            )

            if referred_by:
                self._add_referral_bonus(conn, referred_by)

    def _add_referral_bonus(self, conn: sqlite3.Connection, referred_by: int):
        """Начислить бонус за реферала"""
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (REFERRAL_BONUS, referred_by)
        )
        conn.execute(
            "INSERT INTO transactions (user_id, type, amount, game_type) VALUES (?, ?, ?, ?)",
            (referred_by, "referral_bonus", REFERRAL_BONUS, "referral")
        )

    def update_balance(self, user_id: int, amount: int, game_type: str = "other"):
        """Обновить баланс пользователя и записать транзакцию"""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE users SET balance = balance + ?, games_played = games_played + 1 WHERE user_id = ?",
                (amount, user_id)
            )

            transaction_type = "win" if amount > 0 else "bet"
            self._add_transaction(conn, user_id, transaction_type, abs(amount), game_type)

    def _add_transaction(self, conn: sqlite3.Connection, user_id: int,
                        transaction_type: str, amount: int, game_type: str):
        """Добавить запись о транзакции"""
        conn.execute(
            "INSERT INTO transactions (user_id, type, amount, game_type) VALUES (?, ?, ?, ?)",
            (user_id, transaction_type, amount, game_type)
        )

    def get_top_players(self, limit: int = 10):
        """Получить топ игроков по балансу"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT username, balance, games_played 
                FROM users 
                ORDER BY balance DESC 
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def get_last_bonus_time(self, user_id: int) -> float:
        """Получить время последнего получения бонуса"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT last_bonus_time FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result['last_bonus_time'] if result and result['last_bonus_time'] else 0

    def update_bonus_time(self, user_id: int) -> None:
        """Обновить время получения бонуса"""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_bonus_time = ? WHERE user_id = ?",
                (time.time(), user_id)
            )

    def give_bonus(self, user_id: int, amount: int) -> None:
        """Выдать бонус пользователю"""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
            self._add_transaction(conn, user_id, "bonus", amount, "bonus")
