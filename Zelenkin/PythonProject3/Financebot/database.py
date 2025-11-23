import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица транзакций (расходы)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Таблица доходов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS incomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    source TEXT NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Таблица бюджетов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, category)
                )
            ''')

            conn.commit()

    def add_user(self, user_id: int, username: str, first_name: str):
        """Добавление пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name) 
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            conn.commit()

    def add_expense(self, user_id: int, amount: float, category: str, comment: str = None):
        """Добавление расхода"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO expenses (user_id, amount, category, comment)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, category, comment))
            conn.commit()
            return cursor.lastrowid

    def add_income(self, user_id: int, amount: float, source: str, comment: str = None):
        """Добавление дохода"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO incomes (user_id, amount, source, comment)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, source, comment))
            conn.commit()
            return cursor.lastrowid

    def delete_expense(self, expense_id: int, user_id: int):
        """Удаление расхода"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM expenses 
                WHERE id = ? AND user_id = ?
            ''', (expense_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_today_expenses(self, user_id: int) -> List[Dict]:
        """Получение расходов за сегодня"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM expenses 
                WHERE user_id = ? AND date(created_at) = date('now')
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_week_expenses(self, user_id: int) -> List[Dict]:
        """Получение расходов за неделю"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM expenses 
                WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_month_expenses(self, user_id: int) -> List[Dict]:
        """Получение расходов за текущий месяц"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM expenses 
                WHERE user_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_expenses(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение последних расходов"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, amount, category, comment, created_at
                FROM expenses 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def set_budget(self, user_id: int, category: str, amount: float):
        """Установка бюджета для категории"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO budgets (user_id, category, amount)
                VALUES (?, ?, ?)
            ''', (user_id, category, amount))
            conn.commit()

    def get_budgets(self, user_id: int) -> List[Dict]:
        """Получение бюджетов пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, amount
                FROM budgets 
                WHERE user_id = ?
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_category_spending_vs_budget(self, user_id: int, category: str) -> Dict:
        """Получение трат по категории относительно бюджета"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Получаем бюджет
            cursor.execute('''
                SELECT amount FROM budgets 
                WHERE user_id = ? AND category = ?
            ''', (user_id, category))
            budget_row = cursor.fetchone()
            budget = budget_row['amount'] if budget_row else 0

            # Получаем траты за текущий месяц
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as spent
                FROM expenses 
                WHERE user_id = ? AND category = ? 
                AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            ''', (user_id, category))
            spent_row = cursor.fetchone()
            spent = spent_row['spent'] if spent_row else 0

            return {
                'budget': budget,
                'spent': spent,
                'remaining': budget - spent,
                'percentage': (spent / budget * 100) if budget > 0 else 0
            }