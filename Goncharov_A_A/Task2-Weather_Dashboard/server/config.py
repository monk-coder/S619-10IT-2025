"""
Конфигурация для Weather Dashboard Backend
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secret-key-change-in-production-12345")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"


# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./weather_dashboard.db")

# JWT настройки
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# CORS настройки
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")

# API ключи
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "23e3c51c7e73edad91f3fbbc8fe0562a")

# Настройки приложения
APP_NAME = "Aegis Weather API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "API для космического дашборда погоды"
