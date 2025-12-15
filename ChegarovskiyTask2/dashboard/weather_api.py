import requests
<<<<<<< HEAD
from django.utils import timezone
from .models import WeatherCache


def get_weather_data(city_name):
    # Сначала проверяем кэш
    try:
        cached_weather = WeatherCache.objects.filter(city_name__iexact=city_name).first()
        if cached_weather and cached_weather.is_valid():
            data = cached_weather.weather_data
            data['cached'] = True
            return data
    except Exception as e:
        print(f"Ошибка при проверке кэша: {e}")

    # API ключ прямо здесь
    api_key = "bbcb7dce118f4a659e3ee8a82bb0a384"
    base_url = "http://api.openweathermap.org/data/2.5/weather"

    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)

        if response.status_code == 401:
            print("Ошибка 401: Неверный API ключ")
            return None
        elif response.status_code == 404:
            print("Город не найден")
            return None
        elif response.status_code != 200:
            print(f"Ошибка API: {response.status_code}")
            return None

        data = response.json()

=======
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache

def get_weather_data(city_name):
    if not city_name or not city_name.strip():
        return None

    cached_data = get_cached_weather_data(city_name)
    if cached_data:
        return cached_data

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return None

    try:
        response = requests.get(
            settings.OPENWEATHER_API_URL,
            params={
                'q': city_name,
                'appid': api_key,
                'units': 'metric',
                'lang': 'ru'
            },
            timeout=10
        )
        
        if not response.ok:
            return None
            
        data = response.json()
        
        required_fields = ['name', 'main', 'weather']
        if not all(field in data for field in required_fields):
            return None
            
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
        weather_info = {
            'city': data['name'],
            'temperature': round(data['main']['temp']),
            'description': data['weather'][0]['description'].capitalize(),
            'icon': data['weather'][0]['icon'],
            'humidity': data['main']['humidity'],
            'feels_like': round(data['main']['feels_like']),
            'wind_speed': data['wind']['speed'],
            'cached': False
        }
<<<<<<< HEAD

        # Сохраняем в кэш
        try:
            WeatherCache.objects.update_or_create(
                city_name=city_name,
                defaults={'weather_data': weather_info, 'cached_at': timezone.now()}
            )
        except Exception as e:
            print(f"Ошибка при сохранении в кэш: {e}")

        return weather_info

    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Ошибка в структуре данных: {e}")
        return None


=======
        
        save_to_cache(city_name, weather_info)
        return weather_info
        
    except requests.exceptions.RequestException:
        return None
    except (KeyError, ValueError):
        return None

>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
def get_cached_weather_data(city_name):
    try:
        cached_weather = WeatherCache.objects.filter(city_name__iexact=city_name).first()
        if cached_weather and cached_weather.is_valid():
            data = cached_weather.weather_data
            data['cached'] = True
            return data
<<<<<<< HEAD
    except Exception as e:
        print(f"Ошибка при получении из кэша: {e}")
    return None
=======
    except Exception:
        print(f"Ошибка при получении кэша для города: {city_name}")
    return None

def save_to_cache(city_name, weather_info):
    try:
        WeatherCache.objects.update_or_create(
            city_name=city_name,
            defaults={
                'weather_data': weather_info,
                'cached_at': timezone.now()
            }
        )
    except Exception:
        print(f"Ошибка при сохранении кэша для города: {city_name}")
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
