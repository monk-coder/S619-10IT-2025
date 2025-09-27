import requests
import logging
from django.conf import settings
from django.core.cache import cache
from .models import WeatherCache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherService:
    """Сервис для работы с погодными данными"""
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.cache_duration = settings.WEATHER_CACHE_DURATION
    
    def get_weather(self, city):
        """
        Получает погодные данные для города
        Сначала проверяет кэш, затем обращается к API
        """
        try:
            # Проверяем кэш в базе данных
            cached_weather = self._get_cached_weather(city)
            if cached_weather and not cached_weather.is_expired():
                return self._format_weather_data(cached_weather)
            
            # Если кэш истек или отсутствует, запрашиваем данные с API
            weather_data = self._fetch_from_api(city)
            
            # Сохраняем в кэш
            self._save_to_cache(city, weather_data)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Ошибка при получении погоды для города {city}: {str(e)}")
            raise WeatherAPIException(f"Не удалось получить данные о погоде для города {city}")
    
    def _get_cached_weather(self, city):
        """Получает кэшированные данные из базы"""
        try:
            return WeatherCache.objects.filter(city__iexact=city).first()
        except Exception as e:
            logger.error(f"Ошибка при получении кэша для города {city}: {str(e)}")
            return None
    
    def _fetch_from_api(self, city):
        """Запрашивает данные с OpenWeatherMap API"""
        if not self.api_key or self.api_key == 'demo_key_for_testing':
            raise WeatherAPIException("API ключ не настроен. Пожалуйста, добавьте ваш OpenWeatherMap API ключ в настройки.")
        
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'ru'
        }
        
        logger.info(f"Запрос к API: {self.base_url} с параметрами: {params}")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            logger.info(f"Ответ API: статус {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Данные API: {data}")
                return self._format_api_response(data)
            else:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 404:
                    raise WeatherAPIException(f"Город '{city}' не найден")
                elif status_code == 401:
                    raise WeatherAPIException("Неверный API ключ. Проверьте правильность ключа.")
                elif status_code == 429:
                    raise WeatherAPIException("Превышен лимит запросов к API")
                else:
                    raise WeatherAPIException(f"Ошибка API: {status_code}")
            else:
                raise WeatherAPIException("Сервис погоды временно недоступен")
    
    def _format_api_response(self, data):
        """Форматирует ответ API в нужный формат"""
        return {
            'city': data['name'],
            'country': data['sys']['country'],
            'temperature': round(data['main']['temp'], 1),
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'].title(),
            'icon': data['weather'][0]['icon'],
            'wind_speed': data['wind']['speed'],
            'pressure': data['main']['pressure'],
            'feels_like': round(data['main']['feels_like'], 1),
            'temp_min': round(data['main']['temp_min'], 1),
            'temp_max': round(data['main']['temp_max'], 1),
        }
    
    def _format_weather_data(self, cached_weather):
        """Форматирует кэшированные данные"""
        return {
            'city': cached_weather.city,
            'country': cached_weather.country,
            'temperature': cached_weather.temperature,
            'humidity': cached_weather.humidity,
            'description': cached_weather.description,
            'icon': cached_weather.icon,
            'wind_speed': cached_weather.wind_speed,
            'pressure': cached_weather.pressure,
            'cached': True,
            'cached_at': cached_weather.cached_at,
        }
    
    def _save_to_cache(self, city, weather_data):
        """Сохраняет данные в кэш"""
        try:
            # Удаляем старые записи для этого города
            WeatherCache.objects.filter(city__iexact=city).delete()
            
            # Создаем новую запись
            WeatherCache.objects.create(
                city=weather_data['city'],
                country=weather_data['country'],
                temperature=weather_data['temperature'],
                humidity=weather_data['humidity'],
                description=weather_data['description'],
                icon=weather_data['icon'],
                wind_speed=weather_data['wind_speed'],
                pressure=weather_data['pressure'],
            )
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш: {str(e)}")


class WeatherAPIException(Exception):
    """Исключение для ошибок API погоды"""
    pass
