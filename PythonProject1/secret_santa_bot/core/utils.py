import random
import string
from datetime import datetime


def generate_game_code(length=6):
    """Генерация уникального кода игры"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def validate_date(date_string):
    """Валидация даты в формате ДД.ММ.ГГГГ"""
    try:
        datetime.strptime(date_string, '%d.%m.%Y')
        return True
    except ValueError:
        return False


def format_participant_info(participant, index):
    """Форматирование информации об участнике"""
    user_id, username, full_name, bio, wishlist_count, total_items = participant

    text = f"{index}. {full_name or 'Без имени'}"

    if username:
        text += f" (@{username})"

    if bio and bio != 'None':
        bio_preview = bio[:50] + "..." if len(bio) > 50 else bio
        text += f"\n   📝 {bio_preview}"

    if total_items > 0:
        text += f"\n   🎁 Пунктов в вишлисте: {total_items}"
    else:
        text += f"\n   📝 Вишлист пуст"

    return text


def shuffle_participants(participant_ids):
    """Случайное распределение участников с проверкой, чтобы никто не дарил сам себе"""
    if len(participant_ids) < 2:
        return []

    recipients = participant_ids.copy()
    max_attempts = 100

    for attempt in range(max_attempts):
        random.shuffle(recipients)

        # Проверяем, что никто не дарит сам себе
        valid = True
        for i in range(len(participant_ids)):
            if participant_ids[i] == recipients[i]:
                valid = False
                break

        if valid:
            return list(zip(participant_ids, recipients))

    # Если не удалось найти идеальное распределение, делаем коррекцию
    for i in range(len(participant_ids)):
        if participant_ids[i] == recipients[i]:
            # Меняем с соседним
            next_index = (i + 1) % len(participant_ids)
            recipients[i], recipients[next_index] = recipients[next_index], recipients[i]

    return list(zip(participant_ids, recipients))
    return text