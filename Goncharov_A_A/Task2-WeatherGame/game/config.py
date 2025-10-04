from dataclasses import dataclass, asdict
from datetime import timedelta
from typing import Dict


@dataclass(frozen=True)
class UpgradeDefinition:
    key: str
    name: str
    description: str
    base_cost: int


API_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = ""  # заполните перед запуском
API_TIMEOUT = 10
WEATHER_CACHE_DURATION = timedelta(hours=2)
DEFAULT_WEATHER_UNITS = "metric"
DEFAULT_WEATHER_LANG = "ru"

COINS_PER_FLOOR = 1
FLOOR_BUFFER = 50
MAX_FLOOR_TRAVEL_BURST = 300
WEATHER_LOOKUP_PRICE = 250
MAX_HISTORY_ENTRIES = 10

UPGRADE_CATALOG: Dict[str, UpgradeDefinition] = {}


def as_public_config() -> dict:
    return {
        "coinsPerFloor": COINS_PER_FLOOR,
        "floorBuffer": FLOOR_BUFFER,
        "weatherLookupPrice": WEATHER_LOOKUP_PRICE,
        "upgrades": [asdict(u) for u in UPGRADE_CATALOG.values()],
    }
