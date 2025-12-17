import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Django
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    
    # API Keys
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
    
    @classmethod
    def validate(cls):
        """Проверка наличия обязательных переменных"""
        required_vars = ['SECRET_KEY', 'WEATHER_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        
        print("✓ Все обязательные переменные окружения загружены")

# Валидация при импорте
try:
    Config.validate()
except ValueError as e:
    print(f"⚠️  ВНИМАНИЕ: {e}")