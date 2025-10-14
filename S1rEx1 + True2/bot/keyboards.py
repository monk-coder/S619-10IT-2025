from __future__ import annotations

from typing import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


PREDEFINED_PROMPTS: list[tuple[str, str]] = [
    ("Шпаргалка", "Составь краткий конспект по теме: {topic}. Структурируй в виде пунктов."),
    (
        "Глубокое погружение",
        "Проанализируй тему {topic}. Дай подробный конспект с примерами, вопросами для самопроверки и дополнительными источниками.",
    ),
    (
        "Учитель",
        "Выступи в роли преподавателя и объясни тему {topic} простыми словами. Используй аналогии и заверши кратким тестом.",
    ),
]


def build_prompt_picker(custom_prompts: Sequence[tuple[int, str]]) -> InlineKeyboardMarkup:
    inline_keyboard = [[InlineKeyboardButton(text="Пропустить", callback_data="prompt:skip")]]

    for prompt_id, name in custom_prompts:
        inline_keyboard.append(
            [InlineKeyboardButton(text=name, callback_data=f"prompt:custom:{prompt_id}")]
        )

    for index, (title, _) in enumerate(PREDEFINED_PROMPTS):
        inline_keyboard.append([InlineKeyboardButton(text=title, callback_data=f"prompt:pre:{index}")])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def build_prompts_list_keyboard(custom_prompts: Sequence[tuple[int, str]]) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text=name, callback_data=f"prompt:delete:{prompt_id}")]
        for prompt_id, name in custom_prompts
    ]

    if not inline_keyboard:
        inline_keyboard = [[InlineKeyboardButton(text="Нет сохранённых промптов", callback_data="noop")]]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
