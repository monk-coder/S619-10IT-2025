"""Responses for instructor mode."""


def instructor_intro() -> str:
    return (
        "👨‍🏫 **Режим Инструктора**\n\n"
        "Введите тему, которую хотите изучить:"
    )


def instructor_level_prompt(topic: str) -> str:
    return (
        f"📚 Тема: **{topic}**\n\n"
        "Выберите уровень сложности:"
    )


def instructor_followup_prompt() -> str:
    return "Что дальше?"
