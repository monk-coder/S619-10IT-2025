import requests
import logging
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache

logger = logging.getLogger(__name__)

def get_weather_data(city):
    """
    Получает данные о погоде через OpenWeatherMap API
    """
    # Проверка наличия API ключа
    if not hasattr(settings, 'WEATHER_API_KEY') or not settings.WEATHER_API_KEY:
        logger.error("API ключ OpenWeatherMap не настроен в settings.py")
        return None
    
    # Проверка входных данных
    if not city or not isinstance(city, str) or not city.strip():
        logger.error(f"Некорректное название города: {city}")
        return None
    
    city_lower = city.lower().strip()
    
    # Проверка кэша
    try:
        cached = WeatherCache.objects.get(city=city_lower)
        if cached.is_valid():
            logger.info(f"Используем кэш для города: {city}")
            return cached.weather_data
        else:
            logger.info(f"Кэш для {city} устарел, обновляем данные")
    except WeatherCache.DoesNotExist:
        logger.info(f"Кэш для {city} не найден, запрашиваем данные")
        pass
    except Exception as e:
        logger.error(f"Ошибка при проверке кэша для {city}: {str(e)}")
    
    # Получение реальных данных от API
    logger.info(f"Запрос к OpenWeatherMap API для города: {city}")
    real_data = get_real_weather_data(city)
    
    if real_data:
        # Сохранение в кэш
        try:
            WeatherCache.objects.update_or_create(
                city=city_lower,
                defaults={'weather_data': real_data, 'last_updated': timezone.now()}
            )
            logger.info(f"Данные для {city} сохранены в кэш")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш для {city}: {str(e)}")
    else:
        logger.error(f"Не удалось получить данные для города: {city}")
    
    return real_data

def get_real_weather_data(city):
    """
    Получает реальные данные от OpenWeatherMap API
    """
    # Проверка наличия API ключа
    if not hasattr(settings, 'WEATHER_API_KEY') or not settings.WEATHER_API_KEY:
        logger.error("API ключ OpenWeatherMap не настроен")
        return None
    
    # Проверка входных данных
    if not city or not isinstance(city, str) or not city.strip():
        logger.error(f"Некорректное название города: {city}")
        return None
    
    try:
        api_key = settings.WEATHER_API_KEY
        
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric',
            'lang': 'ru'
        }
        
        logger.info(f"Отправляем запрос к OpenWeatherMap API для города: {city}")
        
        # Выполнение запроса с таймаутом
        response = requests.get(url, params=params, timeout=15)
        
        logger.info(f"Статус ответа от API: {response.status_code}")
        
        # Обработка различных статус-кодов
        if response.status_code == 200:
            data = response.json()
            
            # Проверка структуры ответа
            required_keys = ['main', 'weather', 'name']
            for key in required_keys:
                if key not in data:
                    logger.error(f"Отсутствует ключ '{key}' в ответе API для города: {city}")
                    return None
            
            # Создание структурированных данных
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
            
            logger.info(f"Успешно получены данные: {weather_data['city']} - {weather_data['temperature']}°C")
            return weather_data
            
        elif response.status_code == 404:
            logger.error(f"Город '{city}' не найден в OpenWeatherMap")
            return None
        elif response.status_code == 401:
            logger.error("Неверный или просроченный API ключ OpenWeatherMap")
            return None
        elif response.status_code == 429:
            logger.error("Превышен лимит запросов к OpenWeatherMap API")
            return None
        elif response.status_code >= 500:
            logger.error(f"Ошибка сервера OpenWeatherMap: {response.status_code}")
            return None
        else:
            logger.error(f"Неожиданная ошибка API: {response.status_code}")
            logger.error(f"Текст ошибки: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"Таймаут запроса к OpenWeatherMap API для города: {city}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Ошибка соединения с OpenWeatherMap API для города: {city}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса для города {city}: {str(e)}")
        return None
    except KeyError as e:
        logger.error(f"Отсутствует ключ в ответе API для города {city}: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Ошибка парсинга JSON для города {city}: {str(e)}")
        return None
    except TypeError as e:
        logger.error(f"Ошибка типа данных для города {city}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке города {city}: {str(e)}")
        return None