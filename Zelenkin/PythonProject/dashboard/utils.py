import requests
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache


class WeatherService:
    def __init__(self):
        config = settings.OPENWEATHER_CONFIG
        self.api_key = config['API_KEY']
        self.base_url = config['BASE_URL']
        self.timeout = config['TIMEOUT']
        self.units = config['UNITS']
        self.lang = config['LANG']
        self.cache_timeout = config['CACHE_TIMEOUT']

    def get_weather(self, city, cache=None):
        cache_key = f"weather_{city.lower()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        try:
            params = {
                'q': city,
                'appid': self.api_key,
                'units': self.units,
                'lang': self.lang
            }

            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            weather_data = response.json()
            cache.set(cache_key, weather_data, self.cache_timeout)

            return weather_data
        except requests.exceptions.RequestException as e:
            return {'error': f'Ошибка при получении погоды: {str(e)}'}

    # noinspection PyBroadException
    @staticmethod
    def _get_cached_weather(city_name):
        """Получить данные из кэша"""
        try:
            cached = WeatherCache.objects.filter(city_name__iexact=city_name).first()
            if cached and not cached.is_expired():
                return cached.weather_data
        except Exception:
            pass
        return None

    def _fetch_from_api(self, city_name):
        """Запрос данных от OpenWeatherMap API"""
        params = {
            'q': city_name,
            'appid': self.api_key,
            'units': 'metric',  # для градусов Цельсия
            'lang': 'ru'  # русский язык
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {'error': 'Город не найден. Проверьте название.'}
            elif response.status_code == 401:
                return {'error': 'Неверный API ключ. Проверьте настройки.'}
            else:
                return {'error': f'Ошибка API: {response.status_code}'}

        except requests.exceptions.RequestException:
            return {'error': 'Ошибка соединения с сервисом погоды'}

    @staticmethod
    def _cache_weather_data(weather_data):
        """Кэширование данных погоды"""
        try:
            if 'error' in weather_data:
                return

            city_name = weather_data['name']
            country = weather_data['sys']['country']
            main_data = weather_data['main']
            weather_info = weather_data['weather'][0]

            WeatherCache.objects.update_or_create(
                city_name=city_name,
                defaults={
                    'country': country,
                    'temperature': main_data['temp'],
                    'humidity': main_data['humidity'],
                    'description': weather_info['description'],
                    'icon': weather_info['icon'],
                    'weather_data': weather_data,
                    'cached_at': timezone.now()
                }
            )
        except Exception as e:
            print(f"Ошибка кэширования: {e}")

    @staticmethod
    def format_weather_display(weather_data):
        """Форматирование данных для отображения"""
        if 'error' in weather_data:
            return weather_data

        try:
            weather = weather_data['weather'][0]
            main = weather_data['main']
            wind = weather_data.get('wind', {})

            return {
                'city': weather_data['name'],
                'country': weather_data['sys']['country'],
                'temperature': round(main['temp']),
                'humidity': main['humidity'],
                'description': weather['description'].capitalize(),
                'icon': weather['icon'],
                'icon_url': f"https://openweathermap.org/img/wn/{weather['icon']}@2x.png",
                'feels_like': round(main['feels_like']),
                'pressure': main['pressure'],
                'wind_speed': wind.get('speed', 0),
                'success': True
            }
        except (KeyError, TypeError):
            return {'error': 'Неверный формат данных от погодного сервиса'}