"""Модели данных"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: float


@dataclass
class Transaction:
    id: Optional[int]
    user_id: int
    type: str  # 'expense' or 'income'
    category: Optional[str]
    amount: float
    comment: Optional[str]
    created_at: float


@dataclass
class Budget:
    user_id: int
    category: str
    amount: float