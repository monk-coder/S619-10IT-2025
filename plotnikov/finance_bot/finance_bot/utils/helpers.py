"""Вспомогательные функции"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from config import MAX_LOG_LEN, EXPENSE_CATEGORIES


def now_ts() -> float:
    return time.time()


def clip(text: Optional[str]) -> str:
    """Обрезает текст для логов"""
    if text is None:
        return ""
    sanitized = text.replace("\n", "\\n")
    if len(sanitized) <= MAX_LOG_LEN:
        return sanitized
    return sanitized[:MAX_LOG_LEN] + "…"


def parse_amount(value: str) -> float:
    """Парсит сумму из строки"""
    normalized = value.replace(" ", "").replace(",", ".")
    amount = float(normalized)
    if amount <= 0:
        raise ValueError("amount must be positive")
    return round(amount, 2)


def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999000)


def month_bounds(dt: datetime) -> Tuple[datetime, datetime]:
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if dt.month == 12:
        end_month = start.replace(year=dt.year + 1, month=1)
    else:
        end_month = start.replace(month=dt.month + 1)
    end = end_month - timedelta(microseconds=1000)
    return start, end


# Словари категорий
CATEGORY_INFO: Dict[str, Tuple[str, str]] = {
    key: (emoji, title) for key, emoji, title in EXPENSE_CATEGORIES
}

CATEGORY_ALIASES: Dict[str, str] = {}
for key, emoji, title in EXPENSE_CATEGORIES:
    CATEGORY_ALIASES[key] = key
    CATEGORY_ALIASES[emoji] = key
    CATEGORY_ALIASES[title.lower()] = key
    CATEGORY_ALIASES[title.lower().replace("ё", "е")] = key


def resolve_category(name: str) -> Optional[str]:
    return CATEGORY_ALIASES.get(name.lower())


def aggregate_by_category(rows) -> Dict[str, float]:
    totals = {}
    for row in rows:
        category = row["category"] or "other"
        totals[category] = totals.get(category, 0.0) + float(row["amount"])
    return totals


def render_bar(percent: float) -> str:
    if percent <= 0:
        return ""
    blocks = max(1, int(percent // 5))
    return "█" * min(blocks, 20)


def format_category_line(category: str, amount: float, percent: float) -> str:
    emoji, title = CATEGORY_INFO.get(category, ("✨", category.capitalize()))
    bar = render_bar(percent)
    return f"{emoji} {title}: {amount:.2f}₽ {bar} {percent:.0f}%"