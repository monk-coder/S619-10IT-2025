import os
import sys
import time
import logging
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.append(str(project_root))


def setup_logging():
    """Настройка логирования для службы"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "bot_service.log"),
            logging.StreamHandler()
        ]
    )


def main():
    """Основная функция службы"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("🚀 Запуск Secret Santa Bot как службы...")

    try:
        from core.bot import SecretSantaBot
        bot = SecretSantaBot()
        logger.info("✅ Бот инициализирован, запускаем...")
        bot.run()

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        # Перезапуск через 60 секунд
        time.sleep(60)
        main()


if __name__ == '__main__':
    main()