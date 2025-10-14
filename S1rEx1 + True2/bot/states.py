from aiogram.fsm.state import State, StatesGroup


class ManualNoteStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()


class AiNoteStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_prompt_name = State()


class PromptTemplateStates(StatesGroup):
    waiting_for_template = State()


class CustomPromptStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_template = State()
