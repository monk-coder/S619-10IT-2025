import json
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from bot.database.models import User, GameHistory, Transaction, Base
from bot.config import Config


class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)


class UserOperations:
    def __init__(self, session):
        self.session = session

    async def get_user(self, user_id: int) -> User:
        return self.session.query(User).filter(User.user_id == user_id).first()

    async def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None) -> User:
        user = await self.get_user(user_id)
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            self.session.add(user)
            self.session.commit()
        return user

    async def update_balance(self, user_id: int, amount: float) -> bool:
        user = await self.get_user(user_id)
        if user:
            user.balance += amount
            user.updated_at = func.now()
            self.session.commit()
            return True
        return False

    async def get_balance(self, user_id: int) -> float:
        user = await self.get_user(user_id)
        return user.balance if user else 0.0


class GameOperations:
    def __init__(self, session):
        self.session = session

    async def add_game_record(self, user_id: int, game_type: str, bet_amount: float,
                              win_amount: float = 0, result_data: dict = None):
        record = GameHistory(
            user_id=user_id,
            game_type=game_type,
            bet_amount=bet_amount,
            win_amount=win_amount,
            result_data=json.dumps(result_data) if result_data else None
        )
        self.session.add(record)

        # Обновляем статистику пользователя
        user = self.session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.games_played += 1
            user.total_bets += bet_amount
            user.total_winnings += win_amount
            user.updated_at = func.now()

        self.session.commit()

    async def get_user_stats(self, user_id: int) -> dict:
        user = self.session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {}

        # Получаем последние игры
        recent_games = self.session.query(GameHistory).filter(
            GameHistory.user_id == user_id
        ).order_by(GameHistory.created_at.desc()).limit(10).all()

        return {
            'balance': user.balance,
            'games_played': user.games_played,
            'total_winnings': user.total_winnings,
            'total_bets': user.total_bets,
            'recent_games': recent_games
        }