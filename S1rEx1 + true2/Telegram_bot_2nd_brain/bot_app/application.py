"""Main Telegram bot application assembly."""
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import config, validate_config
from database import DatabaseManager, init_database
from .handlers import (
    DocumentHandlers,
    GeneralHandlers,
    InstructorHandlers,
    MainMenuHandlers,
    NavigationMixin,
    NotesHandlers,
    ProfileHandlers,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, config.log_level),
)


class TelegramBot(
    NavigationMixin,
    MainMenuHandlers,
    ProfileHandlers,
    NotesHandlers,
    DocumentHandlers,
    InstructorHandlers,
    GeneralHandlers,
):
    """Assembled Telegram bot with modular handlers."""

    (MAIN_MENU, PROFILE_MENU, NOTES_TOPIC, NOTES_CONTENT, INSTRUCTOR_TOPIC, INSTRUCTOR_QUESTION, PROMPT_SETTING, INSTRUCTIONS_SETTING) = range(8)

    def __init__(self) -> None:
        self.app: Application | None = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_manager_class = DatabaseManager

    async def post_init(self, application: Application) -> None:  # pragma: no cover - startup hook
        await init_database()
        self.logger.info("Database initialized")

    def setup_handlers(self) -> None:
        conversation = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                self.MAIN_MENU: [
                    CallbackQueryHandler(self.main_menu_callback),
                    MessageHandler(filters.Document.PDF | filters.PHOTO, self.handle_document),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message),
                ],
                self.PROFILE_MENU: [
                    CallbackQueryHandler(self.profile_menu_callback),
                ],
                self.NOTES_TOPIC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notes_topic),
                ],
                self.NOTES_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notes_content),
                ],
                self.INSTRUCTOR_TOPIC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_instructor_topic),
                ],
                self.INSTRUCTOR_QUESTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_instructor_question),
                ],
                self.PROMPT_SETTING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_prompt),
                ],
                self.INSTRUCTIONS_SETTING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_instructions),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.back_to_main_menu, pattern="^back_to_main$"),
            ],
        )

        assert self.app is not None  # for type checkers
        self.app.add_handler(conversation)
        self.app.add_error_handler(self.error_handler)

    def run(self) -> None:
        """Build and run the Telegram bot."""
        if not validate_config():
            return

        self.app = (
            Application.builder()
            .token(config.telegram_token)
            .post_init(self.post_init)
            .build()
        )

        self.setup_handlers()

        self.logger.info("Starting bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


__all__ = ["TelegramBot"]
