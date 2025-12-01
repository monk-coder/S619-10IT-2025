import sqlite3
import contextlib
from config import DB_PATH

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextlib.contextmanager
def db_session():
    conn = connect_db()
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db_session() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at REAL
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                type TEXT CHECK(type IN ('expense', 'income')),
                category TEXT,
                amount REAL CHECK(amount > 0),
                comment TEXT,
                created_at REAL
            );
            CREATE TABLE IF NOT EXISTS budgets (
                user_id INTEGER,
                category TEXT,
                amount REAL CHECK(amount > 0),
                PRIMARY KEY (user_id, category)
            );
        """)

init_db()