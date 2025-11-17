from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, AsyncGenerator
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime,
    Boolean, JSON, ForeignKey, Float, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import config
from pydantic import BaseModel, Field

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('ix_users_telegram_id', 'telegram_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))

    custom_prompt = Column(Text, default="")
    specific_instructions = Column(Text, default="")
    preferred_model = Column(String(255), default="")
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.7)

    total_messages = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class Note(Base):
    __tablename__ = 'notes'
    __table_args__ = (
        Index('ix_notes_user_id', 'user_id'),
        Index('ix_notes_user_created', 'user_id', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    topic = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)  # AI-generated summary
    tags = Column(JSON, default=list)  # List of tags
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="notes")


class Conversation(Base):
    """Conversation history model"""
    __tablename__ = 'conversations'
    __table_args__ = (
        Index('ix_conversations_user_id', 'user_id'),
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    mode = Column(String(50))  # 'instructor', 'notes', 'pdf_extract', etc.
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_message_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message history model"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    role = Column(String(20))
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    
    file_type = Column(String(20))
    file_path = Column(String(500))
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    conversation = relationship("Conversation", back_populates="messages")


engine = None
AsyncSessionLocal = None


async def init_database():
    global engine, AsyncSessionLocal

    pool_kwargs = {}
    if not config.database_url.startswith('sqlite'):
        pool_kwargs = {
            'pool_size': 20,
            'max_overflow': 10,
            'pool_pre_ping': True,
            'pool_recycle': 3600
        }

    engine = create_async_engine(
        config.database_url,
        echo=False,
        **pool_kwargs
    )
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session


class DatabaseManager:
    """Manager class for database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_user(self, telegram_id: int, **kwargs) -> User:
        from sqlalchemy import select
        from sqlalchemy.dialects.sqlite import insert

        stmt = insert(User).values(telegram_id=telegram_id, **kwargs)
        stmt = stmt.on_conflict_do_update(
            index_elements=['telegram_id'],
            set_={'last_active': datetime.now(timezone.utc)}
        )
        await self.session.execute(stmt)
        await self.session.commit()

        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one()
    
    async def update_user_profile(self, telegram_id: int, **kwargs) -> bool:
        """Update user profile settings"""
        from sqlalchemy import select, update
        
        stmt = update(User).where(User.telegram_id == telegram_id).values(**kwargs)
        await self.session.execute(stmt)
        await self.session.commit()
        return True
    
    async def create_note(self, user_id: int, topic: str, content: str, summary: Optional[str] = None) -> Note:
        """Create a new note"""
        note = Note(
            user_id=user_id,
            topic=topic,
            content=content,
            summary=summary
        )
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return note
    
    async def get_user_notes(self, user_id: int, topic: Optional[str] = None) -> List[Note]:
        """Get user notes, optionally filtered by topic"""
        from sqlalchemy import select
        
        stmt = select(Note).where(Note.user_id == user_id)
        if topic:
            stmt = stmt.where(Note.topic == topic)
        stmt = stmt.order_by(Note.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_conversation(self, user_id: int, mode: str) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(user_id=user_id, mode=mode)
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation
    
    async def add_message(self, conversation_id: int, role: str, content: str, 
                         tokens_used: int = 0, file_type: Optional[str] = None,
                         file_path: Optional[str] = None) -> Message:
        """Add a message to a conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            file_type=file_type,
            file_path=file_path
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def get_conversation_history(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """Get conversation history"""
        from sqlalchemy import select
        
        stmt = select(Message).where(Message.conversation_id == conversation_id)
        stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        return list(reversed(messages))
    
    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        from sqlalchemy import select, func
        
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return {}

        notes_stmt = select(func.count(Note.id)).where(Note.user_id == user_id)
        notes_result = await self.session.execute(notes_stmt)
        notes_count = notes_result.scalar()
        
        conv_stmt = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        conv_result = await self.session.execute(conv_stmt)
        conv_count = conv_result.scalar()
        
        return {
            'total_messages': user.total_messages,
            'total_tokens_used': user.total_tokens_used,
            'notes_count': notes_count,
            'conversations_count': conv_count,
            'member_since': user.created_at,
            'last_active': user.last_active
        }
