"""Работа с базой данных"""
import sqlite3
import threading
from typing import List, Optional, Tuple
from config import DB_PATH

DB_LOCK = threading.Lock()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema() -> None:
    with DB_LOCK:
        db = get_db()
        db.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
                category TEXT,
                amount REAL NOT NULL,
                comment TEXT,
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_user_created_at
                ON transactions(user_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS budgets (
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                PRIMARY KEY (user_id, category)
            );

            CREATE TABLE IF NOT EXISTS budget_alerts (
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                period TEXT NOT NULL,
                threshold TEXT NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(user_id, category, period, threshold)
            );
        """)
        db.commit()


# Инициализация базы при импорте
ensure_schema()