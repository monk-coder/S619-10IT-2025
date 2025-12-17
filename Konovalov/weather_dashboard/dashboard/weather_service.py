import requests
import logging
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache

logger = logging.getLogger(__name__)

def get_weather_data(city):
    """Получает данные о погоде"""
    try:

        if not hasattr(settings, 'WEATHER_API_KEY') or not settings.WEATHER_API_KEY:
            raise ValueError("API ключ не настроен")
        
        if not hasattr(settings, 'WEATHER_API_URL') or not settings.WEATHER_API_URL:
            raise ValueError("URL API не настроен")
        
        city_lower = city.lower().strip()
        

        try:
            cache = WeatherCache.objects.get(city=city_lower)
            if cache.is_valid():
                logger.info(f"Кэш для {city}")
                return cache.weather_data
        except WeatherCache.DoesNotExist:
            pass
        

        response = requests.get(
            settings.WEATHER_API_URL,  # URL из настроек
            params={
                'q': city,
                'appid': settings.WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ru'
            },
            timeout=10
        )
        response.raise_for_status()  # Проверка статуса
        
        data = response.json()
        result = {
            'city': data['name'],
            'temperature': round(data['main']['temp']),
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'country': data['sys']['country'],
            'feels_like': round(data['main']['feels_like']),
            'wind_speed': data['wind']['speed'],
            'pressure': data['main']['pressure']
        }
        

        WeatherCache.objects.update_or_create(
            city=city_lower,
            defaults={'weather_data': result}
        )
        
        logger.info(f"Данные для {result['city']} получены")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка для {city}: {type(e).__name__}: {str(e)}")
        return None