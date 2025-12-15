import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_project.settings')
django.setup()

from dashboard.weather_api import get_weather_data

# Тестируем разные города
test_cities = ["Moscow", "London", "Paris", "Berlin"]

for city in test_cities:
    print(f"\n--- Тестируем город: {city} ---")
    result = get_weather_data(city)
    if result:
        print(f"УСПЕХ: {result}")
    else:
        print(f"ОШИБКА: Не удалось получить данные для '{city}'")
        print("Проверьте API ключ и интернет-соединение")