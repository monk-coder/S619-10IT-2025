"""Операции с базой данных."""
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from config import DB_PATH
from database.models import Game

# Блокировка для потокобезопасности
DB_LOCK = threading.Lock()

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

DB = get_db()

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

# Вспомогательные функции
def now_ts() -> float:
    return time.time()

# Операции с пользователями
def ensure_user(user_id: int, username: Optional[str]) -> None:
    with DB_LOCK:
        row = DB.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            if username:
                DB.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
                DB.commit()
            return
        DB.execute(
            "INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
            (user_id, username, now_ts()),
        )
        DB.commit()

def update_profile(user_id: int, full_name: str, bio: str) -> None:
    with DB_LOCK:
        DB.execute(
            "UPDATE users SET full_name = ?, bio = ? WHERE user_id = ?",
            (full_name, bio, user_id),
        )
        DB.commit()

def get_profile(user_id: int) -> sqlite3.Row:
    with DB_LOCK:
        return DB.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

# Операции с вишлистом
def list_wishlist(user_id: int) -> List[sqlite3.Row]:
    with DB_LOCK:
        return DB.execute(
            "SELECT id, description, photo_file_id FROM wish_items WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()

def add_wish_item(user_id: int, description: str, photo_file_id: Optional[str]) -> None:
    with DB_LOCK:
        DB.execute(
            "INSERT INTO wish_items (user_id, description, photo_file_id, created_at) VALUES (?, ?, ?, ?)",
            (user_id, description.strip(), photo_file_id, now_ts()),
        )
        DB.commit()

def delete_wish_item(user_id: int, item_id: int) -> bool:
    with DB_LOCK:
        cur = DB.execute(
            "DELETE FROM wish_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        )
        DB.commit()
        return cur.rowcount > 0

# Операции с играми
def generate_game_code() -> str:
    import secrets
    return secrets.token_hex(3).upper()

def create_game(owner_id: int, title: str, draw_date: str, minimum: int) -> Game:
    code = generate_game_code()
    with DB_LOCK:
        DB.execute(
            "INSERT INTO games (code, owner_id, title, draw_date, min_participants, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (code, owner_id, title.strip(), draw_date.strip(), max(3, minimum), now_ts()),
        )
        DB.commit()
        row = DB.execute(
            "SELECT id, code, owner_id, title, draw_date, min_participants FROM games WHERE code = ?",
            (code,),
        ).fetchone()
    return Game(**dict(row))

def find_game_by_code(code: str) -> Optional[Game]:
    with DB_LOCK:
        row = DB.execute(
            "SELECT id, code, owner_id, title, draw_date, min_participants FROM games WHERE code = ?",
            (code.upper(),),
        ).fetchone()
    return Game(**dict(row)) if row else None

def add_participant(game_id: int, user_id: int) -> bool:
    with DB_LOCK:
        try:
            DB.execute(
                "INSERT INTO game_participants (game_id, user_id, joined_at) VALUES (?, ?, ?)",
                (game_id, user_id, now_ts()),
            )
            DB.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_participant(game_id: int, user_id: int) -> bool:
    with DB_LOCK:
        if DB.execute("SELECT 1 FROM matches WHERE game_id = ?", (game_id,)).fetchone():
            return False
        cur = DB.execute(
            "DELETE FROM game_participants WHERE game_id = ? AND user_id = ?",
            (game_id, user_id),
        )
        DB.commit()
        return cur.rowcount > 0

def list_participants(game_id: int) -> List[int]:
    with DB_LOCK:
        rows = DB.execute(
            "SELECT user_id FROM game_participants WHERE game_id = ? ORDER BY joined_at",
            (game_id,),
        ).fetchall()
    return [row["user_id"] for row in rows]

def store_matches(game_id: int, pairs: Dict[int, int]) -> None:
    with DB_LOCK:
        DB.execute("DELETE FROM matches WHERE game_id = ?", (game_id,))
        DB.executemany(
            "INSERT INTO matches (game_id, santa_id, recipient_id, created_at) VALUES (?, ?, ?, ?)",
            [(game_id, santa, recipient, now_ts()) for santa, recipient in pairs.items()],
        )
        DB.commit()

def get_match(game_id: int, santa_id: int) -> Optional[int]:
    with DB_LOCK:
        row = DB.execute(
            "SELECT recipient_id FROM matches WHERE game_id = ? AND santa_id = ?",
            (game_id, santa_id),
        ).fetchone()
    return row["recipient_id"] if row else None

def get_games_for_owner(owner_id: int) -> List[Game]:
    with DB_LOCK:
        rows = DB.execute(
            "SELECT id, code, owner_id, title, draw_date, min_participants FROM games WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,),
        ).fetchall()
    return [Game(**dict(row)) for row in rows]

def get_participating_games(user_id: int) -> List[Game]:
    with DB_LOCK:
        rows = DB.execute(
            """
            SELECT g.id, g.code, g.owner_id, g.title, g.draw_date, g.min_participants
            FROM games g
            JOIN game_participants gp ON gp.game_id = g.id
            WHERE gp.user_id = ?
            ORDER BY g.created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [Game(**dict(row)) for row in rows]