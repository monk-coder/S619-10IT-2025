"""Handler mixins for the Telegram bot."""

from .navigation import NavigationMixin
from .main_menu import MainMenuHandlers
from .profile import ProfileHandlers
from .notes import NotesHandlers
from .documents import DocumentHandlers
from .instructor import InstructorHandlers
from .general import GeneralHandlers

__all__ = [
    "NavigationMixin",
    "MainMenuHandlers",
    "ProfileHandlers",
    "NotesHandlers",
    "DocumentHandlers",
    "InstructorHandlers",
    "GeneralHandlers",
]
