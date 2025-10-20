"""Responses for main menu interactions."""

from __future__ import annotations


def welcome_message(first_name: str | None) -> str:
    name = first_name or "друг"
    return (
        f"👋 Привет, {name}!\n\n"
        "eto umniy bot\n"
        "Выберите режим работы:"
    )


def main_menu_prompt() -> str:
    return "🏠 **Главное меню**\n\nВыберите режим работы:"
