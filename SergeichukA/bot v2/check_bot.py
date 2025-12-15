#!/usr/bin/env python3
"""
Скрипт для проверки корректности настройки бота
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Проверяет настройки окружения"""
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ Токен бота не найден в .env файле")
        print("📝 Создай файл .env с содержимым:")
        print("TELEGRAM_BOT_TOKEN=твой_токен_здесь")
        return False
    
    if token == "your_telegram_bot_token_here":
        print("❌ Ты не изменил токен в .env файле!")
        print("🔧 Замени 'your_telegram_bot_token_here' на настоящий токен")
        return False
    
    print("✅ Настройки окружения в порядке")
    return True

def check_bot_connection():
    """Проверяет соединение с Telegram API"""
    import requests
    from config import BOT_TOKEN
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data["result"]
            print(f"✅ Бот подключен: @{bot_info['username']} ({bot_info['first_name']})")
            return True
        else:
            print(f"❌ Ошибка Telegram API: {data.get('description')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка настроек бота...")
    
    if check_environment() and check_bot_connection():
        print("🎉 Все проверки пройдены! Бот готов к работе.")
        print("🚀 Запускай: python main.py")
    else:
        print("💥 Найдены проблемы. Исправь их перед запуском.")
        sys.exit(1)