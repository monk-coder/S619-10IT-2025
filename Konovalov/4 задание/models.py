from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@dataclass
class Transaction:
    id: Optional[int] = None
    user_id: int = 0
    type: str = ""
    category: Optional[str] = None
    amount: float = 0.0
    comment: Optional[str] = None
    created_at: float = 0.0

@dataclass
class Budget:
    user_id: int
    category: str
    amount: float