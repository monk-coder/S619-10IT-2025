from typing import List, Dict
from config import CATEGORIES


def format_amount(amount: float) -> str:
    """Форматирование суммы"""
    return f"{amount:.2f}₽".replace('.00', '')


def create_bar_chart(percentage: float, max_length: int = 10) -> str:
    """Создание текстового графика"""
    filled = int(percentage / 100 * max_length)
    return '█' * filled + '░' * (max_length - filled)


def format_statistics(expenses: List[Dict], period: str) -> str:
    """Форматирование статистики"""
    if not expenses:
        return f"📊 Расходы за {period} отсутствуют"

    total = sum(expense['total'] for expense in expenses)

    result = [f"📊 <b>Расходы за {period}</b>\n"]
    result.append(f"<b>Всего:</b> {format_amount(total)}\n")

    for expense in expenses:
        category_name = CATEGORIES.get(expense['category'], expense['category'])
        percentage = (expense['total'] / total * 100) if total > 0 else 0
        bar = create_bar_chart(percentage)

        result.append(
            f"{category_name}: {format_amount(expense['total'])} "
            f"{bar} {percentage:.1f}%"
        )

    # Добавляем средние значения для месяца
    if period == "месяц":
        from datetime import datetime
        today = datetime.now().day
        avg_per_day = total / today
        result.append(f"\n<b>Средний расход в день:</b> {format_amount(avg_per_day)}")

    return "\n".join(result)


def format_history(expenses: List[Dict]) -> str:
    """Форматирование истории транзакций"""
    if not expenses:
        return "📝 История транзакций пуста"

    result = ["📝 <b>Последние транзакции:</b>\n"]

    for expense in expenses:
        date = expense['created_at'][:16]  # Обрезаем до даты и времени
        category_name = CATEGORIES.get(expense['category'], expense['category'])
        comment = f" - {expense['comment']}" if expense['comment'] else ""

        result.append(
            f"• {date}\n"
            f"  {category_name}: {format_amount(expense['amount'])}{comment}"
        )

    return "\n".join(result)


def parse_amount(text: str) -> float:
    """Парсинг суммы из текста"""
    try:
        # Убираем все нецифровые символы кроме точки и запятой
        cleaned = ''.join(c for c in text if c.isdigit() or c in ',.')
        # Заменяем запятую на точку
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except (ValueError, TypeError):
        raise ValueError("Неверный формат суммы. Введите число, например: 500 или 150.50")