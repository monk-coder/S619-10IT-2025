from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class User:
    user_id: int
    username: str
    chat_id: int
    score: int = 0
    coins: int = 0
    energy: int = 100
    max_energy: int = 100
    last_energy_update: int = None
    level: int = 1
    total_clicks: int = 0
    double_click: int = 1
    auto_clicker: int = 0
    fast_recovery: int = 1
    last_auto_click: int = 0
    last_daily_bonus: int = 0
    consecutive_days: int = 0
    invited_by: Optional[int] = None
    invite_count: int = 0

    def __post_init__(self):
        if self.last_energy_update is None:
            self.last_energy_update = int(time.time())


class ShopItem:
    ITEMS = {
        'double_click': {
            'name': 'Двойной клик',
            'price': 100,
            'description': '+2 очка за каждый клик',
            'effect': {'double_click': 2}
        },
        'auto_clicker': {
            'name': 'Автокликер',
            'price': 500,
            'description': '+1 очко в секунду',
            'effect': {'auto_clicker': 1}
        },
        'max_energy': {
            'name': 'Больше энергии',
            'price': 300,
            'description': 'Максимум энергии 200',
            'effect': {'max_energy': 200}
        },
        'fast_recovery': {
            'name': 'Быстрое восстановление',
            'price': 400,
            'description': '2 энергии в минуту',
            'effect': {'fast_recovery': 2}
        }
    }