"""Entry point for the Telegram bot application."""

from bot_app import TelegramBot

def main() -> None:
    """Run the Telegram bot."""
    TelegramBot().run()


if __name__ == "__main__":
    main()


def factorial(n: int) -> int:
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)
