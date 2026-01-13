from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

__all__ = [
    "UpgradeDefinition",
    "UPGRADE_CATALOG",
    "get_upgrade_definition",
    "next_level_cost",
]


@dataclass(frozen=True)
class UpgradeDefinition:
    key: str
    name: str
    description: str
    base_cost: int
    cost_increment: int = 0
    max_level: Optional[int] = 1
    metadata: Dict[str, float] = field(default_factory=dict)

    def cost_for_level(self, current_level: int) -> int:
        multiplier = max(current_level, 0)
        cost = self.base_cost + self.cost_increment * multiplier
        return max(cost, 0)


UPGRADE_CATALOG: Dict[str, UpgradeDefinition] = {
    "superlift": UpgradeDefinition(
        key="superlift",
        name="Суперлифты",
        description="Автоматический подъём на +100 этажtq за уровень каждые 5 секунд.",
        base_cost=500,
        cost_increment=350,
        max_level=3,
        metadata={"floors_per_level": 1, "interval_ms": 5000},
    ),
    "weather_radar": UpgradeDefinition(
        key="weather_radar",
        name="Радар погоды",
        description="Снижает стоимость просмотра погоды на 20% за уровень (минимум 100 монет).",
        base_cost=400,
        cost_increment=300,
        max_level=4,
        metadata={"discount_per_level": 0.2, "min_price": 100},
    ),
    "coin_collector": UpgradeDefinition(
        key="coin_collector",
        name="Коллектор монет",
        description="Дополнительные 15% монет за этаж за каждый уровень.",
        base_cost=600,
        cost_increment=400,
        max_level=5,
        metadata={"bonus_per_level": 0.15},
    ),
    "task_slot": UpgradeDefinition(
        key="task_slot",
        name="Органайзер задач",
        description="Открывает +1 слот задач на город за покупку.",
        base_cost=200,
        cost_increment=150,
        max_level=8,
        metadata={"tasks_per_level": 1},
    ),
}


def get_upgrade_definition(key: str) -> UpgradeDefinition:
    if key not in UPGRADE_CATALOG:
        raise KeyError(f"Неизвестное улучшение: {key}")
    return UPGRADE_CATALOG[key]


def next_level_cost(key: str, current_level: int) -> int:
    definition = get_upgrade_definition(key)
    return definition.cost_for_level(current_level)
