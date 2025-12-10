import requests
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache

def get_weather_data(city):
    """
    Получает данные о погоде через OpenWeatherMap API
    """
    city_lower = city.lower().strip()
    
    # Проверяем кэш
    try:
        cached = WeatherCache.objects.get(city=city_lower)
        if cached.is_valid():
            print(f"🔄 Используем кэш для {city}")
            return cached.weather_data
    except WeatherCache.DoesNotExist:
        pass
    
    print(f"🌍 Запрос к OpenWeatherMap API для города: {city}")
    
    # Получаем реальные данные от OpenWeatherMap API
    real_data = get_real_weather_data(city)
    if not real_data:
        # Если API не сработало, возвращаем ошибку
        print(f"❌ Не удалось получить данные для {city}")
        return None
    
    # Сохраняем в кэш
    try:
        WeatherCache.objects.update_or_create(
            city=city_lower,
            defaults={'weather_data': real_data}
        )
    except Exception as e:
        print(f"❌ Ошибка сохранения в кэш: {e}")
    
    return real_data

def get_real_weather_data(city):
    """
    Получает реальные данные от OpenWeatherMap API
    """
    try:
        api_key = settings.WEATHER_API_KEY
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric',
            'lang': 'ru'
        }
        
        print(f"🔗 Отправляем запрос к OpenWeatherMap API для города: {city}")
        response = requests.get(url, params=params, timeout=15)
        
        print(f"📡 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            weather_data = {
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
            
            print(f"✅ Получены реальные данные: {data['name']} - {weather_data['temperature']}°C, {weather_data['description']}")
            print(f"📊 Детали: влажность {weather_data['humidity']}%, ветер {weather_data['wind_speed']} м/с")
            return weather_data
            
        elif response.status_code == 404:
            print(f"❌ Город '{city}' не найден в OpenWeatherMap")
            return None
        elif response.status_code == 401:
            print(f"❌ Неверный API ключ OpenWeatherMap")
            return None
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📄 Текст ответа: {response.text[:200]}...")
            return None
            
    except requests.exceptions.Timeout:
        print(f"⏰ Таймаут запроса к OpenWeatherMap API для {city}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"🔌 Ошибка соединения с OpenWeatherMap API для {city}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка для {city}: {e}")
        return None

def translate_condition(condition):
    """
    Переводит условия погоды (уже получаем на русском от API)
    """
    return condition

def get_icon_mapping(icon_code):
    """
    Возвращает код иконки OpenWeatherMap (уже в правильном формате)
    """
    return icon_code