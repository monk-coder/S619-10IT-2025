"""Responses for document processing flows."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def extract_mode_intro() -> str:
    return (
        "📄 **Извлечение информации**\n\n"
        "Отправьте фото или PDF документ для обработки.\n"
        "Я извлеку текст и создам краткое содержание.\n\n"
        "Для отмены напишите /cancel"
    )


def unsupported_document_message() -> str:
    return "⚠️ Поддерживаются только PDF документы и изображения."


def processing_message() -> str:
    return "⏳ Обрабатываю документ..."


def document_processed_message(
    metadata: Mapping[str, Any],
    summary: str,
    key_points: Sequence[str] | None = None,
) -> str:
    doc_type = metadata.get("type", "Неизвестно")
    page_count = metadata.get("page_count")
    clipped_summary = summary[:500]

    parts = ["✅ **Документ обработан**\n\n", f"**Тип:** {doc_type}\n"]

    if page_count:
        parts.append(f"**Страниц:** {page_count}\n")

    parts.append(f"\n**Краткое содержание:**\n{clipped_summary}\n\n")

    if key_points:
        parts.append("**Ключевые пункты:**\n")
        for index, point in enumerate(key_points[:5], start=1):
            parts.append(f"{index}. {point[:100]}\n")

    return "".join(parts)


def document_processing_error(error: str | None = None) -> str:
    details = f": {error}" if error else ""
    return f"❌ Ошибка обработки документа{details}"
