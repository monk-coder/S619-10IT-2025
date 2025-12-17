import requests
import logging
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache

logger = logging.getLogger(__name__)

def get_weather_data(city):
    """Получает данные о погоде через OpenWeatherMap API"""
    try:
       
        if not getattr(settings, 'WEATHER_API_KEY', None):
            logger.error("API ключ OpenWeatherMap не настроен")
            return None
        
     
        if not isinstance(city, str) or not city.strip():
            logger.error(f"Некорректное название города: {city}")
            return None
        
        city_lower = city.lower().strip()
        
       
        try:
            cached = WeatherCache.objects.get(city=city_lower)
            if (timezone.now() - cached.last_updated).total_seconds() < 7200:
                logger.info(f"Используем кэш для города: {city}")
                return cached.weather_data
        except:
            pass
        
   
        logger.info(f"Запрос к OpenWeatherMap API для города: {city}")
        
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                'q': city,
                'appid': settings.WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ru'
            },
            timeout=10
        )
        
      
        if response.status_code != 200:
            logger.error(f"API ошибка: {response.status_code} для города {city}")
            return None
        
    
        data = response.json()
        weather_data = {
            'city': data.get('name', city),
            'temperature': round(data['main']['temp']),
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'country': data.get('sys', {}).get('country', ''),
            'feels_like': round(data['main']['feels_like']),
            'wind_speed': data.get('wind', {}).get('speed', 0),
            'pressure': data['main'].get('pressure')
        }
        
        logger.info(f"Получены данные: {weather_data['city']} - {weather_data['temperature']}°C")
        

        try:
            WeatherCache.objects.update_or_create(
                city=city_lower,
                defaults={'weather_data': weather_data, 'last_updated': timezone.now()}
            )
        except:
            logger.warning(f"Не удалось сохранить в кэш для {city}")
        
        return weather_data
        
    except Exception as e:
        
        logger.error(f"Ошибка при получении погоды для {city}: {str(e)}")
        return None
