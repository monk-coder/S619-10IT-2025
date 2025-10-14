"""Centralized prompt templates for AI interactions."""
from typing import Optional


GENERAL_ASSISTANT_PROMPT = "You are a helpful educational assistant."


def summary_system_prompt(max_length: int) -> str:
    """Prompt for generating concise summaries."""
    return (
        "You are a helpful assistant that creates concise summaries.\n"
        f"Create a summary of the following text in no more than {max_length} characters.\n"
        "Focus on the key points and main ideas."
    )


def image_extraction_system_prompt() -> str:
    """Prompt for extracting structured data from images."""
    return (
        "You are a helpful assistant that extracts and structures information.\n"
        "When given a description of an image, extract the key information and present it in a clear, structured format."
    )


def contextual_answer_system_prompt(custom_instructions: Optional[str]) -> str:
    """Prompt for answering questions with given context."""
    base_prompt = (
        "You are a knowledgeable educational assistant.\n"
        "Answer questions based on the provided context. Be accurate and helpful."
    )
    if custom_instructions:
        base_prompt += f"\n\nAdditional instructions: {custom_instructions}"
    return base_prompt


def instructor_system_prompt(topic: str, level: str, custom_instructions: Optional[str]) -> str:
    """Prompt for instructor mode explanations."""
    base_prompt = (
        f"You are an expert instructor teaching about {topic}.\n"
        f"Adapt your explanation to the {level} level.\n"
        "Be clear, provide examples, and check understanding.\n"
        "Use structured explanations with clear sections."
    )
    if custom_instructions:
        base_prompt += f"\n\nAdditional instructions: {custom_instructions}"
    return base_prompt
