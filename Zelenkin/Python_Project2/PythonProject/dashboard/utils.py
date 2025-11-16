# dashboard/utils.py
import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.timeout = getattr(settings, 'OPENWEATHER_TIMEOUT', 10)

    def get_weather(self, city):
        """Получение погоды по городу с кэшированием"""
        if not city or not isinstance(city, str):
            return {'error': 'Название города не может быть пустым'}

        cache_key = f"weather_{city.lower().strip()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(f"Using cached weather data for {city}")
            return cached_data

        # Проверяем API ключ
        if not self.api_key or self.api_key == 'your_default_api_key_here':
            return {'error': 'API ключ не настроен. Проверьте настройки OpenWeatherMap.'}

        try:
            params = {
                'q': city.strip(),
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'ru'
            }

            logger.info(f"Fetching weather for {city} from API")
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )

            # Проверяем статус ответа
            if response.status_code == 200:
                weather_data = response.json()

                # Кэшируем на 2 часа (7200 секунд)
                cache.set(cache_key, weather_data, 7200)
                logger.info(f"Weather data fetched and cached for {city}")

                return weather_data
            elif response.status_code == 401:
                return {'error': 'Неверный API ключ OpenWeatherMap'}
            elif response.status_code == 404:
                return {'error': f'Город "{city}" не найден'}
            elif response.status_code == 429:
                return {'error': 'Превышен лимит запросов к API'}
            else:
                return {'error': f'Ошибка API: {response.status_code}'}

        except requests.exceptions.ConnectionError:
            return {'error': 'Ошибка подключения к серверу погоды'}
        except requests.exceptions.Timeout:
            return {'error': 'Таймаут при запросе погоды'}
        except requests.exceptions.RequestException as e:
            return {'error': f'Ошибка при получении погоды: {str(e)}'}
        except ValueError:
            return {'error': 'Ошибка обработки данных погоды'}

    @staticmethod
    def format_weather_display(weather_data):
        """Форматирование данных погоды для отображения"""
        if 'error' in weather_data:
            return weather_data

        try:
            return {
                'city': weather_data['name'],
                'country': weather_data['sys']['country'],
                'temperature': round(weather_data['main']['temp']),
                'feels_like': round(weather_data['main']['feels_like']),
                'humidity': weather_data['main']['humidity'],
                'pressure': weather_data['main']['pressure'],
                'description': weather_data['weather'][0]['description'].title(),
                'icon': weather_data['weather'][0]['icon'],
                'wind_speed': weather_data['wind']['speed'],
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error formatting weather data: {str(e)}")
            return {'error': 'Неверный формат данных погоды'}