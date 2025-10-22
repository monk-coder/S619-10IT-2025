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
    if cached_data := cache.get(cache_key):
        logger.info(f"Кэш найден для города: {city}")
        return cached_data

    if not settings.OPENWEATHER_API_KEY:
        raise Exception("OPENWEATHER_API_KEY не установлен")

    response = _make_weather_api_request(city)

    weather_data = _process_weather_response(response, city)

    _cache_weather_data(cache_key, weather_data)
    logger.info(f"Данные сохранены в кэш для города: {city} (Часовой пояс: {weather_data['timezone_info']})")

    return weather_data



class WeatherAPIError(Exception):
    pass

class CityNotFoundError(WeatherAPIError):
    pass

class RateLimitExceededError(WeatherAPIError):
    pass

class ServerError(WeatherAPIError):
    pass

def _process_weather_response(response, city):
    try:
        response.raise_for_status()
    except Exception as e:
        if response.status_code == 404:
            raise CityNotFoundError("Город не найден. Пожалуйста, проверьте название.") from e
        elif response.status_code == 429:
            raise RateLimitExceededError("Превышен лимит запросов к OpenWeatherMap") from e
        elif response.status_code >= 500:
            return _handle_api_server_error(city)
        else:
            raise WeatherAPIError(f"Произошла ошибка: {response.status_code}") from e

    data = response.json()
    return data
    if 'main' not in data or 'weather' not in data:
        raise Exception("Некорректный ответ от сервиса погоды")

    return _build_weather_data(data)


def _handle_api_server_error(city):
    old_cache_key = f"weather_{city.lower().strip()}_old"
    if old_data := cache.get(old_cache_key):
        logger.warning(f"OpenWeatherMap недоступен, возвращаем старые данные для: {city}")
        return old_data
    else:
        raise Exception("Сервис погоды временно недоступен")


def _build_weather_data(data):
    rain_probability = _calculate_rain_probability(data)

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
    tz_offset_seconds = data.get('timezone', 0)
    city_tz = dt_timezone(timedelta(seconds=tz_offset_seconds))
    current_time_in_city = datetime.now(city_tz)

    tz_hours = tz_offset_seconds // 3600
    timezone_str = f"UTC{tz_hours:+d}" if tz_hours != 0 else "UTC"

    return timezone_str, current_time_in_city


def _cache_weather_data(cache_key, weather_data):"
    cache.set(cache_key, weather_data, 7200)  # 2 часа
    cache.set(f"{cache_key}_old", weather_data, 21600)  # 6 часов



