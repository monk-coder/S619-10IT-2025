from typing import Optional

MARKDOWN_INSTRUCTIONS = """
Format all text to markdown. Be concise and honest.
For code snippets, use: ```language\ncode\n```
"""

GENERAL_ASSISTANT_PROMPT = f"You are a helpful educational assistant.{MARKDOWN_INSTRUCTIONS}"


def summary_system_prompt(max_length: int | None = None) -> str:
    length_hint = f"\nKeep the summary under {max_length} characters." if max_length else ""
    return (
        "You are a helpful assistant that creates concise summaries.\n"
        "Focus on the key points and main ideas."
        f"{length_hint}"
        f"{MARKDOWN_INSTRUCTIONS}"
    ).strip()


def image_extraction_system_prompt() -> str:
    return (
        "You are a helpful assistant that extracts and structures information.\n"
        "When given a description of an image, extract the key information and present it in a clear, structured format."
        f"{MARKDOWN_INSTRUCTIONS}"
    )


def contextual_answer_system_prompt(custom_instructions: Optional[str]) -> str:
    base = (
        "You are a knowledgeable educational assistant.\n"
        "Answer questions based on the provided context. Be accurate and helpful."
        f"{MARKDOWN_INSTRUCTIONS}"
    )
    if custom_instructions:
        base += f"\n\nAdditional instructions: {custom_instructions}"
    return base


def instructor_system_prompt(topic: str, level: str, custom_instructions: Optional[str]) -> str:
    base = (
        f"You are an expert instructor teaching about {topic}.\n"
        f"Adapt your explanation to the {level} level.\n"
        "Be clear, provide examples, and check understanding.\n"
        "Use structured explanations with clear sections."
        f"{MARKDOWN_INSTRUCTIONS}"
    )
    if custom_instructions:
        base += f"\n\nAdditional instructions: {custom_instructions}"
    return base
