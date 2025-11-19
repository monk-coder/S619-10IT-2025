"""Модели данных."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Game:
    id: int
    code: str
    owner_id: int
    title: str
    draw_date: Optional[str]
    min_participants: int