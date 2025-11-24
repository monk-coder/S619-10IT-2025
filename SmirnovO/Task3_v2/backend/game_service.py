import time
from datetime import datetime, timedelta
from database import db
from models import User


class GameService:
    @staticmethod
    def check_achievements(user: User) -> list:
        achievements = []

        if user.total_clicks >= 100 and not db.has_achievement(user.user_id, 'novice'):
            db.add_achievement(user.user_id, 'novice')
            achievements.append('novice')

        if user.total_clicks >= 1000 and not db.has_achievement(user.user_id, 'hardworker'):
            db.add_achievement(user.user_id, 'hardworker')
            achievements.append('hardworker')

        current_time = int(time.time())
        if user.last_daily_bonus == 0 or (current_time - user.last_daily_bonus) >= 86400:
            yesterday = datetime.now() - timedelta(days=1)
            if user.last_daily_bonus >= yesterday.timestamp():
                user.consecutive_days += 1
            else:
                user.consecutive_days = 1

            user.last_daily_bonus = current_time
            user.coins += 50

            if user.consecutive_days >= 7 and not db.has_achievement(user.user_id, 'marathoner'):
                db.add_achievement(user.user_id, 'marathoner')
                achievements.append('marathoner')

        return achievements

    @staticmethod
    def process_click(user: User) -> dict:
        user = db.update_energy(user)

        if user.energy <= 0:
            return {'error': 'No energy'}

        click_reward = user.double_click
        user.energy -= 1
        user.score += click_reward
        user.coins += click_reward
        user.total_clicks += 1

        new_level = user.score // 1000 + 1
        level_up = new_level > user.level
        if level_up:
            user.level = new_level

        achievements = GameService.check_achievements(user)
        db.save_user(user)

        return {
            'new_score': user.score,
            'new_energy': user.energy,
            'new_coins': user.coins,
            'level_up': level_up,
            'new_level': user.level,
            'achievements': achievements
        }