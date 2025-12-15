from __future__ import annotations

import os
from dataclasses import asdict
from datetime import timedelta
from typing import Dict

from ..util.upgrades import (
    UpgradeDefinition,
    UPGRADE_CATALOG,
    get_upgrade_definition,
    next_level_cost,
)

__all__ = [
    "UpgradeDefinition",
    "UPGRADE_CATALOG",
    "get_upgrade_definition",
    "next_level_cost",
    "API_BASE_URL",
    "API_KEY",
    "API_TIMEOUT",
    "WEATHER_CACHE_DURATION",
    "DEFAULT_WEATHER_UNITS",
    "DEFAULT_WEATHER_LANG",
    "COINS_PER_FLOOR",
    "FLOOR_BUFFER",
    "MAX_FLOOR_TRAVEL_BURST",
    "MAX_FLOOR_ABSOLUTE",
    "WEATHER_LOOKUP_PRICE",
    "MAX_HISTORY_ENTRIES",
    "MAX_COIN_BALANCE",
    "weather_lookup_cost",
    "coin_bonus_multiplier",
    "superlift_effect",
    "task_slots",
    "as_public_config",
]


def _env_int(name: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if minimum is not None and value < minimum:
        return minimum
    if maximum is not None and value > maximum:
        return maximum
    return value


API_BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5/weather")
API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
API_TIMEOUT = _env_int("OPENWEATHER_TIMEOUT", 10, minimum=2, maximum=60)
WEATHER_CACHE_DURATION = timedelta(minutes=_env_int("WEATHER_CACHE_MINUTES", 120, minimum=5))
DEFAULT_WEATHER_UNITS = os.getenv("OPENWEATHER_UNITS", "metric")
DEFAULT_WEATHER_LANG = os.getenv("OPENWEATHER_LANG", "ru")

COINS_PER_FLOOR = _env_int("WEATHER_GAME_COINS_PER_FLOOR", 1, minimum=1)
FLOOR_BUFFER = _env_int("WEATHER_GAME_FLOOR_BUFFER", 50, minimum=10, maximum=500)
MAX_FLOOR_TRAVEL_BURST = _env_int("WEATHER_GAME_MAX_FLOOR_BURST", 300, minimum=10, maximum=2000)
MAX_FLOOR_ABSOLUTE = _env_int("WEATHER_GAME_MAX_FLOOR_ABSOLUTE", 500000, minimum=1000)
WEATHER_LOOKUP_PRICE = _env_int("WEATHER_GAME_LOOKUP_PRICE", 250, minimum=10)
MAX_HISTORY_ENTRIES = _env_int("WEATHER_GAME_HISTORY_ENTRIES", 10, minimum=1, maximum=50)
MAX_COIN_BALANCE = _env_int("WEATHER_GAME_MAX_COINS", 1_000_000_000, minimum=1000)


def weather_lookup_cost(level: int) -> int:
    definition = get_upgrade_definition("weather_radar")
    discount = definition.metadata.get("discount_per_level", 0) * level
    price = WEATHER_LOOKUP_PRICE * (1 - discount)
    min_price = definition.metadata.get("min_price", WEATHER_LOOKUP_PRICE)
    return max(int(round(price)), int(min_price))

def coin_bonus_multiplier(level: int) -> float:
    bonus = get_upgrade_definition("coin_collector").metadata.get("bonus_per_level", 0)
    return 1 + bonus * level


def superlift_effect(level: int) -> Dict[str, int]:
    definition = get_upgrade_definition("superlift")
    floors_per_level = int(definition.metadata.get("floors_per_level", 100))
    interval_ms = int(definition.metadata.get("interval_ms", 5000))
    return {
        "floors": floors_per_level * level,
        "interval_ms": interval_ms,
    }


def task_slots(level: int) -> int:
    per_level = int(get_upgrade_definition("task_slot").metadata.get("tasks_per_level", 0))
    return per_level * level


def as_public_config() -> dict:
    return {
        "coinsPerFloor": COINS_PER_FLOOR,
        "floorBuffer": FLOOR_BUFFER,
        "weatherLookupPrice": WEATHER_LOOKUP_PRICE,
        "maxFloor": MAX_FLOOR_ABSOLUTE,
        "maxFloorBurst": MAX_FLOOR_TRAVEL_BURST,
        "maxCoins": MAX_COIN_BALANCE,
        "upgrades": [asdict(u) for u in UPGRADE_CATALOG.values()],
    }
