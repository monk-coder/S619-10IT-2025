# database/db_handler.py
import sqlite3
import logging
import os
from typing import List, Optional
from database.models import User, Transaction, GameHistory

logger = logging.getLogger(__name__)


class DatabaseHandler:
    def __init__(self, db_path: str = 'casino.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Создаем таблицы если их нет
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance INTEGER DEFAULT 1000,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    amount INTEGER,
                    description TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game_type TEXT,
                    bet INTEGER,
                    win INTEGER,
                    result TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            conn.commit()
            logger.info("✅ База данных инициализирована")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        finally:
            if conn:
                conn.close()

    def get_connection(self):
        """Получение соединения с базой данных"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def update_user_balance_direct(self, user_id: int, amount: int) -> bool:
        """Прямое обновление баланса - ПРОСТАЯ И РАБОЧАЯ ВЕРСИЯ"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Сначала убедимся, что пользователь существует
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            user_exists = cursor.fetchone() is not None

            if not user_exists:
                logger.info(f"👤 Создаем пользователя {user_id}")
                cursor.execute(
                    'INSERT INTO users (user_id, balance) VALUES (?, ?)',
                    (user_id, 1000)
                )

            # Получаем текущий баланс
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            current_balance = cursor.fetchone()[0]
            logger.info(f"🔍 Текущий баланс пользователя {user_id}: {current_balance}")

            # Обновляем баланс
            cursor.execute(
                'UPDATE users SET balance = balance + ?, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?',
                (amount, user_id)
            )

            conn.commit()

            # Проверяем результат
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            new_balance = cursor.fetchone()[0]

            logger.info(f"✅ Баланс обновлен: user_id={user_id}, изменение={amount}, новый баланс={new_balance}")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления баланса для пользователя {user_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

                def close_connection(self):
                    """Закрыть соединение с базой данных"""
                    try:
                        # Если есть активные соединения, их можно закрыть здесь
                        # SQLite обычно автоматически закрывает соединения,
                        # но если нужно что-то специфичное, можно добавить сюда
                        logger.info("✅ Соединение с базой данных закрыто")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при закрытии соединения с БД: {e}")

    def update_user_balance(self, user_id: int, amount: int) -> bool:
        """Обновление баланса (алиас для обратной совместимости)"""
        return self.update_user_balance_direct(user_id, amount)
    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """Получение истории транзакций пользователя"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, user_id, type, amount, description, timestamp
                FROM transactions 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))

            transactions = []
            for row in cursor.fetchall():
                transactions.append(Transaction(*row))

            return transactions

        except Exception as e:
            logger.error(f"Error getting transactions for user {user_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_all_users(self, limit: int = 100) -> List[User]:
        """Получение списка всех пользователей"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, username, first_name, last_name, balance, created_at, last_activity
                FROM users 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            users = []
            for row in cursor.fetchall():
                users.append(User(*row))

            return users

        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_balance(self, user_id: int) -> int:
        """Получение баланса пользователя"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                # Создаем пользователя если не существует
                self.create_user(user_id)
                return 1000

        except Exception as e:
            logger.error(f"Ошибка получения баланса для пользователя {user_id}: {e}")
            return 1000
        finally:
            if conn:
                conn.close()

    def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
        """Создание нового пользователя"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, 1000))

            conn.commit()
            logger.info(f"✅ Создан пользователь: {user_id}")

            return self.get_user(user_id)

        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, username, first_name, last_name, balance, created_at, last_activity
                FROM users WHERE user_id = ?
            ''', (user_id,))

            row = cursor.fetchone()
            if row:
                return User(*row)
            return None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_transaction(self, transaction: Transaction) -> bool:
        """Добавление транзакции"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO transactions (user_id, type, amount, description)
                VALUES (?, ?, ?, ?)
            ''', (transaction.user_id, transaction.type, transaction.amount, transaction.description))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def add_game_history(self, game_history: GameHistory) -> bool:
        """Добавление записи в историю игр"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO game_history (user_id, game_type, bet, win, result)
                VALUES (?, ?, ?, ?, ?)
            ''', (game_history.user_id, game_history.game_type, game_history.bet, game_history.win,
                  game_history.result))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error adding game history: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_user_game_history(self, user_id: int, limit: int = 10) -> List[GameHistory]:
        """Получение истории игр пользователя"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, user_id, game_type, bet, win, result, timestamp
                FROM game_history 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))

            history = []
            for row in cursor.fetchall():
                history.append(GameHistory(*row))

            return history

        except Exception as e:
            logger.error(f"Error getting game history for user {user_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()