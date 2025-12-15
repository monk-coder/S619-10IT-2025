"""Responses for note creation workflow."""

from __future__ import annotations

from typing import Iterable


def note_creation_intro() -> str:
    return (
        "📝 **Создание конспекта**\n\n"
        "Отправьте текст, PDF или изображение.\n"
        "Я обработаю материал и сохраню краткий конспект.\n\n"
        "Для отмены напишите /cancel"
    )


def note_processing_message() -> str:
    return "⏳ Обрабатываю материал..."


def unsupported_material_message() -> str:
    return "⚠️ Поддерживаются текстовые сообщения, изображения и PDF файлы."


def note_saved_message(topic: str, summary: str, key_points: Iterable[str] | None = None) -> str:
    clipped_summary = summary[:500]
    message = (
        "✅ Конспект готов и сохранен!\n\n"
        f"**Тема:** {topic}\n\n"
        f"**Краткое содержание:**\n{clipped_summary}"
    )

    if key_points:
        message += "\n\n**Ключевые пункты:**\n"
        for index, point in enumerate(key_points, start=1):
            message += f"{index}. {point[:120]}\n"

    return message.strip()


def note_error_message(details: str | None = None) -> str:
    suffix = f": {details}" if details else ""
    return f"❌ Не удалось обработать материал{suffix}"
