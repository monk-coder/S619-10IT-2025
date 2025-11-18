import sqlite3
import threading
from config import DB_PATH

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

DB = get_db()
DB_LOCK = threading.Lock()

def ensure_schema() -> None:
    with DB_LOCK:
        DB.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                bio TEXT,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wish_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                photo_file_id TEXT,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                owner_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                draw_date TEXT,
                min_participants INTEGER NOT NULL DEFAULT 3,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS game_participants (
                game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                joined_at REAL NOT NULL,
                PRIMARY KEY (game_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS matches (
                game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                santa_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                recipient_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                PRIMARY KEY (game_id, santa_id)
            );
            CREATE TABLE IF NOT EXISTS anonymous_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                santa_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at REAL NOT NULL
            );
        """)
        DB.commit()