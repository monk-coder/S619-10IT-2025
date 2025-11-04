from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    balance = Column(Float, default=1000.0)
    games_played = Column(Integer, default=0)
    total_winnings = Column(Float, default=0.0)
    total_bets = Column(Float, default=0.0)
    last_daily = Column(DateTime)
    referred_by = Column(Integer, nullable=True)
    is_banned = Column(Boolean, default=False)
    language = Column(String(10), default='ru')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class GameHistory(Base):
    __tablename__ = 'game_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    game_type = Column(String(50), nullable=False)
    bet_amount = Column(Float, nullable=False)
    win_amount = Column(Float, default=0.0)
    result_data = Column(Text)  # JSON с деталями игры
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # 'deposit', 'withdraw', 'bonus', 'win'
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)