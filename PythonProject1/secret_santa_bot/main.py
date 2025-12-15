import logging
import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main():
    """Основная функция запуска бота"""
    try:
        print("🚀 Запуск Secret Santa Bot...")

        from core.bot import SecretSantaBot
        bot = SecretSantaBot()
        bot.run()

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Проверьте что все файлы созданы:")
        print("- core/__init__.py")
        print("- core/bot.py")
        print("- core/database.py")
        print("- core/utils.py")
        print("- config.py")
        print("- .env")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()