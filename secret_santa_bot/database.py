from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sqlite3

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(200))
    bio = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class WishlistItem(Base):
    __tablename__ = 'wishlist_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    photo_id = Column(String(300))  # Telegram file_id для фото
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="wishlist_items")

User.wishlist_items = relationship("WishlistItem", order_by=WishlistItem.id, back_populates="user")

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    organizer_id = Column(Integer, ForeignKey('users.id'))
    draw_date = Column(DateTime, nullable=False)
    min_participants = Column(Integer, default=3)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    organizer = relationship("User")
    participants = relationship("Participant", back_populates="game")

class Participant(Base):
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    
    game = relationship("Game", back_populates="participants")
    user = relationship("User")

class SantaPair(Base):
    __tablename__ = 'santa_pairs'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    santa_id = Column(Integer, ForeignKey('users.id'))
    recipient_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    
    game = relationship("Game")
    santa = relationship("User", foreign_keys=[santa_id])
    recipient = relationship("User", foreign_keys=[recipient_id])

class AnonymousQuestion(Base):
    __tablename__ = 'anonymous_questions'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    from_user_id = Column(Integer, ForeignKey('users.id'))
    to_user_id = Column(Integer, ForeignKey('users.id'))
    question = Column(Text, nullable=False)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    game = relationship("Game")
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])

# Инициализация базы данных
engine = create_engine('sqlite:///secret_santa.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()