import sqlite3
import logging
from typing import List, Optional, Dict, Any
from models import User
import config
import time

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = config.Config.DATABASE_URL):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                chat_id INTEGER,
                score INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                max_energy INTEGER DEFAULT 100,
                last_energy_update INTEGER,
                level INTEGER DEFAULT 1,
                total_clicks INTEGER DEFAULT 0,
                double_click INTEGER DEFAULT 1,
                auto_clicker INTEGER DEFAULT 0,
                fast_recovery INTEGER DEFAULT 1,
                last_auto_click INTEGER,
                last_daily_bonus INTEGER,
                consecutive_days INTEGER DEFAULT 0,
                invited_by INTEGER,
                invite_count INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                achievement_name TEXT,
                achieved_at INTEGER,
                PRIMARY KEY (user_id, achievement_name)
            )
        ''')

        conn.commit()
        conn.close()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_user(self, user_id: int) -> Optional[User]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return User(*row)
        return None

    def create_user(self, user_id: int, username: str, chat_id: int, invited_by: int = None) -> User:
        user = User(
            user_id=user_id,
            username=username,
            chat_id=chat_id,
            invited_by=invited_by
        )
        self.save_user(user)
        return user

    def save_user(self, user: User):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user.user_id, user.username, user.chat_id, user.score, user.coins,
            user.energy, user.max_energy, user.last_energy_update, user.level,
            user.total_clicks, user.double_click, user.auto_clicker,
            user.fast_recovery, user.last_auto_click, user.last_daily_bonus,
            user.consecutive_days, user.invited_by, user.invite_count
        ))
        conn.commit()
        conn.close()

    def update_energy(self, user: User) -> User:
        current_time = int(time.time())
        time_diff = current_time - user.last_energy_update

        if time_diff >= 60:
            energy_to_add = (time_diff // 60) * user.fast_recovery
            user.energy = min(user.max_energy, user.energy + energy_to_add)
            user.last_energy_update = current_time - (time_diff % 60)

        return user

    def add_achievement(self, user_id: int, achievement_name: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO achievements VALUES (?, ?, ?)',
            (user_id, achievement_name, int(time.time()))
        )
        conn.commit()
        conn.close()

    def get_achievements(self, user_id: int) -> List[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT achievement_name FROM achievements WHERE user_id = ?',
            (user_id,)
        )
        achievements = [row[0] for row in cursor.fetchall()]
        conn.close()
        return achievements

    def has_achievement(self, user_id: int, achievement_name: str) -> bool:
        return achievement_name in self.get_achievements(user_id)

    def get_leaderboard(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, score, level, total_clicks 
            FROM users 
            ORDER BY score DESC 
            LIMIT ?
        ''', (limit,))

        leaders = []
        for i, (user_id, username, score, level, total_clicks) in enumerate(cursor.fetchall(), 1):
            leaders.append({
                'rank': i,
                'user_id': user_id,
                'username': username,
                'score': score,
                'level': level,
                'total_clicks': total_clicks
            })

        conn.close()
        return leaders

    def get_user_rank(self, user_id: int) -> Optional[int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rank FROM (
                SELECT user_id, ROW_NUMBER() OVER (ORDER BY score DESC) as rank
                FROM users
            ) WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_users_with_auto_clicker(self) -> List[User]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE auto_clicker > 0')
        users = [User(*row) for row in cursor.fetchall()]
        conn.close()
        return users


db = Database()