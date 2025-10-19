"""Response builders for profile-related flows."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping


def profile_menu_intro() -> str:
    return "👤 **Профиль**\n\nВыберите действие:"


def prompt_setting_message() -> str:
    return (
        "⚙️ **Настройка промпта**\n\n"
        "Отправьте новый системный промпт для AI. Полностью будет игнорировать текущий промпт\n"
        "Это повлияет на стиль и поведение ответов.\n\n"
        "Для отмены напишите /cancel"
    )


def instructions_setting_message() -> str:
    return (
        "📋 **Специфические инструкции**\n\n"
        "Zдесь писать рандомную чушь, чтобы попугать маленьких индийский детей, которые будут тебе отвечать.\n"
        "Например: 'Отвечай на петушином языке(кудахтай)' или 'каждые 2 слова восхваляй open source'.\n\n"
        "Для отмены напишите /cancel"
    )


def current_settings_text(
    custom_prompt: str | None,
    instructions: str | None,
    max_tokens: int,
    temperature: float,
) -> str:
    prompt_value = custom_prompt or "Стандартный"
    instructions_value = instructions or "Не заданы"
    return (
        "👁 **Текущие настройки**\n\n"
        f"**Промпт:** {prompt_value}\n\n"
        f"**Инструкции:** {instructions_value}\n\n"
        f"**Max токенов:** {max_tokens}\n"
        f"**Temperature:** {temperature}"
    )


def statistics_text(stats: Mapping[str, Any]) -> str:
    return (
        "📊 **Статистика использования**\n\n"
        f"**Всего сообщений:** {stats.get('total_messages', 0)}\n"
        f"**Токенов использовано:** {stats.get('total_tokens_used', 0)}\n"
        f"**Конспектов создано:** {stats.get('notes_count', 0)}\n"
        f"**Диалогов:** {stats.get('conversations_count', 0)}\n"
        f"**Зарегистрирован:** {stats.get('member_since', 'Неизвестно')}\n"
        f"**Последняя активность:** {stats.get('last_active', 'Неизвестно')}"
    )


def user_info_text(user_context: str | None) -> str:
    if user_context and user_context.strip():
        context_value = escape(user_context.strip())
    else:
        context_value = "Ты пока не рассказал о себе. Нажми кнопку ниже и поделись деталями."

    return (
        "ℹ️ <b>Расскажи о себе</b>\n\n"
        "Расскажи о себе(ноу вей):\n"
        "• На кого учишься или где работаешь?\n"
        "• Какие предметы и темы сейчас приоритетны?\n"
        "• Какой формат объяснений тебе удобен?\n\n"
        "<b>Твоя текущая карточка:</b>\n"
        f"{context_value}"
    )
