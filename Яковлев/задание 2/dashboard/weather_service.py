# dashboard/weather_service.py
import requests
from django.core.cache import cache
from django.conf import settings
from datetime import datetime, timezone as dt_timezone, timedelta
import logging

logger = logging.getLogger(__name__)

def get_weather_data(city):
    """
    Получает данные о погоде с кэшированием на 2 часа.
    Возвращает словарь с данными или raise Exception.
    """
    cache_key = f"weather_{city.lower().strip()}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Кэш найден для города: {city}")
        return cached_data

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        raise Exception("OPENWEATHER_API_KEY не установлен")

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }

    try:
        logger.info(f"Запрос к OpenWeatherMap для города: {city}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            raise Exception("Город не найден. Пожалуйста, проверьте название.")
        elif response.status_code == 429:
            raise Exception("Превышен лимит запросов к OpenWeatherMap")
        elif response.status_code >= 500:
            old_cache_key = f"weather_{city.lower().strip()}_old"
            old_data = cache.get(old_cache_key)
            if old_data:
                logger.warning(f"OpenWeatherMap недоступен, возвращаем старые данные для: {city}")
                return old_data
            else:
                raise Exception("Сервис погоды временно недоступен")
        
        response.raise_for_status()
        data = response.json()

        if 'main' not in data or 'weather' not in data:
            raise Exception("Некорректный ответ от сервиса погоды")

        # === ОПРЕДЕЛЕНИЕ ПОГОДНЫХ УСЛОВИЙ ===
        weather_main = data['weather'][0]['main'].lower()
        weather_description = data['weather'][0]['description'].lower()
    
        # Определяем вероятность дождя (условно)
        rain_probability = 0
        if 'rain' in weather_main or 'drizzle' in weather_main:
            rain_probability = 100  # Идёт дождь
        elif 'shower' in weather_description:
            rain_probability = 80   # Ливень возможен
        elif 'cloud' in weather_description and data['main']['humidity'] > 80:
            rain_probability = 60   # Высокая влажность + облачно
        elif 'cloud' in weather_description:
            rain_probability = 30   # Облачно, возможен дождь
            
        # === КЛЮЧЕВАЯ ЧАСТЬ: ПРАВИЛЬНАЯ ОБРАБОТКА ЧАСОВОГО ПОЯСА ===
        # OpenWeatherMap возвращает timezone в секундах от UTC
        tz_offset_seconds = data.get('timezone', 0)  # Например: 10800 для Москвы (UTC+3)
        
        # Создаём объект часового пояса
        city_tz = dt_timezone(timedelta(seconds=tz_offset_seconds))
        
        # Получаем текущее время в часовом поясе города
        current_time_in_city = datetime.now(city_tz)
        
        # Форматируем для отображения
        formatted_time = current_time_in_city.strftime('%d.%m.%Y %H:%M')
        
        # Также можно показать смещение
        tz_hours = tz_offset_seconds // 3600
        timezone_str = f"UTC{tz_hours:+d}" if tz_hours != 0 else "UTC"
        
        weather = {
            'city': data['name'],
            'temperature': round(data['main']['temp']),
            'humidity': data['main']['humidity'],
            'condition': data['weather'][0]['description'].capitalize(),
            'icon_code': data['weather'][0]['icon'],
            'timestamp': current_time_in_city.isoformat(),
            'formatted_time': formatted_time,
            'timezone_info': timezone_str,
            'source': 'openweathermap',
            'rain_probability': rain_probability,  # ← НОВОЕ ПОЛЕ
            'weather_main': weather_main,          # ← НОВОЕ ПОЛЕ
            'wind_speed': data['wind']['speed'] if 'wind' in data else 0,
        }
        
        cache.set(cache_key, weather, 7200)
        cache.set(f"{cache_key}_old", weather, 21600)
        
        logger.info(f"Данные сохранены в кэш для города: {city} (Часовой пояс: {timezone_str})")
        return weather
        
    except requests.exceptions.Timeout:
        raise Exception("Тайм-аут запроса к сервису погоды")
    except requests.exceptions.ConnectionError:
        raise Exception("Ошибка подключения к сервису погоды")
    except Exception as e:
        logger.error(f"Ошибка при получении погоды для {city}: {str(e)}")
        raise e