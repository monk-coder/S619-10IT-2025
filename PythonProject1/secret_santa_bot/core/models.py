# Простые модели данных для начала
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    user_id: int
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    created_at: datetime

@dataclass
class Game:
    game_code: str
    game_name: str
    organizer_id: int
    draw_date: str
    min_participants: int
    is_active: bool
    created_at: datetime

@dataclass
class Wishlist:
    user_id: int
    items: List['WishlistItem']

@dataclass
class WishlistItem:
    name: str
    description: Optional[str]
    photo_id: Optional[str]