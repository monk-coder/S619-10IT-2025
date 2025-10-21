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
    # Проверка кэша
    cache_key = f"weather_{city.lower().strip()}"
    if cached_data := cache.get(cache_key):
        logger.info(f"Кэш найден для города: {city}")
        return cached_data

    # Валидация API ключа
    if not settings.OPENWEATHER_API_KEY:
        raise Exception("OPENWEATHER_API_KEY не установлен")

    # Выполнение запроса к API
    response = _make_weather_api_request(city)

    # Обработка ответа API
    weather_data = _process_weather_response(response, city)

    # Кэширование и возврат
    _cache_weather_data(cache_key, weather_data)
    logger.info(f"Данные сохранены в кэш для города: {city} (Часовой пояс: {weather_data['timezone_info']})")

    return weather_data


def _make_weather_api_request(city):
    """Выполняет HTTP-запрос к OpenWeatherMap API"""
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': settings.OPENWEATHER_API_KEY,
        'units': 'metric',
        'lang': 'ru'
    }

    logger.info(f"Запрос к OpenWeatherMap для города: {city}")
    try:
        response = requests.get(url, params=params, timeout=10)
        return response
    except requests.exceptions.Timeout:
        raise Exception("Тайм-аут запроса к сервису погоды")
    except requests.exceptions.ConnectionError:
        raise Exception("Ошибка подключения к сервису погоды")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении погоды для {city}: {str(e)}")
        raise Exception(f"Ошибка запроса к сервису погоды: {str(e)}")


def _process_weather_response(response, city):
    """Обрабатывает ответ от API и возвращает структурированные данные погоды"""
    # Обработка ошибок HTTP
    if response.status_code == 404:
        raise Exception("Город не найден. Пожалуйста, проверьте название.")
    elif response.status_code == 429:
        raise Exception("Превышен лимит запросов к OpenWeatherMap")
    elif response.status_code >= 500:
        return _handle_api_server_error(city)

    response.raise_for_status()
    data = response.json()

    # Валидация структуры ответа
    if 'main' not in data or 'weather' not in data:
        raise Exception("Некорректный ответ от сервиса погоды")

    # Создание структурированных данных погоды
    return _build_weather_data(data)


def _handle_api_server_error(city):
    """Обработка ошибок сервера OpenWeatherMap с возвратом кэшированных данных"""
    old_cache_key = f"weather_{city.lower().strip()}_old"
    if old_data := cache.get(old_cache_key):
        logger.warning(f"OpenWeatherMap недоступен, возвращаем старые данные для: {city}")
        return old_data
    else:
        raise Exception("Сервис погоды временно недоступен")


def _build_weather_data(data):
    """Создает структурированный словарь данных погоды из ответа API"""
    # Определение вероятности дождя
    rain_probability = _calculate_rain_probability(data)

    # Обработка часового пояса
    timezone_info, current_time_in_city = _process_timezone(data)
    formatted_time = current_time_in_city.strftime('%d.%m.%Y %H:%M')

    return {
        'city': data['name'],
        'temperature': round(data['main']['temp']),
        'humidity': data['main']['humidity'],
        'condition': data['weather'][0]['description'].capitalize(),
        'icon_code': data['weather'][0]['icon'],
        'timestamp': current_time_in_city.isoformat(),
        'formatted_time': formatted_time,
        'timezone_info': timezone_info,
        'source': 'openweathermap',
        'rain_probability': rain_probability,
        'weather_main': data['weather'][0]['main'].lower(),
        'wind_speed': data['wind']['speed'] if 'wind' in data else 0,
    }


def _calculate_rain_probability(data):
    """Рассчитывает вероятность дождя на основе погодных условий"""
    weather_main = data['weather'][0]['main'].lower()
    weather_description = data['weather'][0]['description'].lower()
    humidity = data['main']['humidity']

    if 'rain' in weather_main or 'drizzle' in weather_main:
        return 100  # Идёт дождь
    elif 'shower' in weather_description:
        return 80  # Ливень возможен
    elif 'cloud' in weather_description and humidity > 80:
        return 60  # Высокая влажность + облачно
    elif 'cloud' in weather_description:
        return 30  # Облачно, возможен дождь
    return 0


def _process_timezone(data):
    """Обрабатывает информацию о часовом поясе из данных API"""
    tz_offset_seconds = data.get('timezone', 0)
    city_tz = dt_timezone(timedelta(seconds=tz_offset_seconds))
    current_time_in_city = datetime.now(city_tz)

    tz_hours = tz_offset_seconds // 3600
    timezone_str = f"UTC{tz_hours:+d}" if tz_hours != 0 else "UTC"

    return timezone_str, current_time_in_city


def _cache_weather_data(cache_key, weather_data):
    """Кэширует данные погоды с основным и резервным ключами"""
    cache.set(cache_key, weather_data, 7200)  # 2 часа
    cache.set(f"{cache_key}_old", weather_data, 21600)  # 6 часов
