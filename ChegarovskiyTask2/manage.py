#!/usr/bin/env python
import os
import sys
from dotenv import load_dotenv

<<<<<<< HEAD

def main():
    """Run administrative tasks."""
    # Загрузка переменных окружения
    load_dotenv()

=======
def main():
    load_dotenv()
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

<<<<<<< HEAD

=======
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
if __name__ == '__main__':
    main()