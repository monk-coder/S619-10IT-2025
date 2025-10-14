"""Entry point for the Telegram bot application."""
from bot_app import TelegramBot


def main() -> None:
    """Run the Telegram bot."""
    TelegramBot().run()


if __name__ == "__main__":
    main()
