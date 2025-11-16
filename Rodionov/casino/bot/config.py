import os
import yaml
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///data/database.db"


@dataclass
class GameConfig:
    min_bet: int
    max_bet: int
    symbols: List[str] = None
    payouts: Dict[str, float] = None


@dataclass
class EconomyConfig:
    start_balance: float = 1000
    daily_bonus_min: int = 50
    daily_bonus_max: int = 200
    referral_bonus: int = 100


class Config:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

        # Загрузка конфига YAML
        self._load_yaml_config()

    def _load_yaml_config(self):
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # Экономика
            economy_data = config_data.get('economy', {})
            self.ECONOMY = EconomyConfig(
                start_balance=economy_data.get('start_balance', 1000),  # ← ИСПРАВЛЕНО
                daily_bonus_min=economy_data.get('daily_bonus_min', 50),
                daily_bonus_max=economy_data.get('daily_bonus_max', 200),
                referral_bonus=economy_data.get('referral_bonus', 100)
            )

            # Настройки игр
            self.GAMES = {}
            games_data = config_data.get('games', {})

            # Слоты
            slots_data = games_data.get('slots', {})
            self.GAMES['slots'] = GameConfig(
                min_bet=slots_data.get('min_bet', 10),
                max_bet=slots_data.get('max_bet', 1000),
                symbols=slots_data.get('symbols', []),
                payouts=slots_data.get('payouts', {})
            )

            # Монетка
            coin_data = games_data.get('coin_flip', {})
            self.GAMES['coin_flip'] = GameConfig(
                min_bet=coin_data.get('min_bet', 1),
                max_bet=coin_data.get('max_bet', 500)
            )

            # Рулетка
            roulette_data = games_data.get('roulette', {})
            self.GAMES['roulette'] = GameConfig(
                min_bet=roulette_data.get('min_bet', 5),
                max_bet=roulette_data.get('max_bet', 1000)
            )

        except FileNotFoundError:
            # Значения по умолчанию если файл не найден
            self._set_defaults()

    def _set_defaults(self):
        self.ECONOMY = EconomyConfig()
        self.GAMES = {
            'slots': GameConfig(
                min_bet=10,
                max_bet=1000,
                symbols=["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "7️⃣"],
                payouts={
                    "7️⃣7️⃣7️⃣": 10,
                    "💎💎💎": 8,
                    "🔔🔔🔔": 5,
                    "🍇🍇🍇": 3
                }
            ),
            'coin_flip': GameConfig(min_bet=1, max_bet=500),
            'roulette': GameConfig(min_bet=5, max_bet=1000)
        }