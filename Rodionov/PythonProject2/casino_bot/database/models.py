# database/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    user_id: int
    balance: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: Optional[str] = None
    last_activity: Optional[str] = None

@dataclass
class Transaction:
    id: Optional[int] = None
    user_id: Optional[int] = None
    type: Optional[str] = None
    amount: Optional[int] = None
    description: Optional[str] = None
    timestamp: Optional[str] = None

@dataclass
class GameHistory:
    id: Optional[int] = None
    user_id: Optional[int] = None
    game_type: Optional[str] = None
    bet: Optional[int] = None
    win: Optional[int] = None
    result: Optional[str] = None
    timestamp: Optional[str] = None