from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
  hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

  tasks: Mapped[list["WeatherTask"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
  history_entries: Mapped[list["CityHistory"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class WeatherTask(Base):
  __tablename__ = "weather_tasks"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
  title: Mapped[str] = mapped_column(String(200), nullable=False)
  city: Mapped[str] = mapped_column(String(120), nullable=False)
  is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

  owner: Mapped[User] = relationship(back_populates="tasks")


class CityHistory(Base):
  __tablename__ = "city_history"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
  city: Mapped[str] = mapped_column(String(120), nullable=False)
  searched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

  owner: Mapped[User] = relationship(back_populates="history_entries")


class CachedWeather(Base):
  __tablename__ = "cached_weather"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  cache_key: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
  payload: Mapped[str] = mapped_column(Text, nullable=False)
  fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
