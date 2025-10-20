import requests
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache


def get_weather_data(city_name):
    if not city_name or not city_name.strip():
        return None

    try:
        cached_weather = WeatherCache.objects.filter(city_name__iexact=city_name).first()
        if cached_weather and cached_weather.is_valid():
            data = cached_weather.weather_data
            data['cached'] = True
            return data
    except Exception:
        pass

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return None

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
            return None
        elif response.status_code == 404:
            return None
        elif response.status_code == 429:
            return None
        elif response.status_code != 200:
            return None

        data = response.json()

        if 'name' not in data or 'main' not in data or 'weather' not in data:
            return None

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

        try:
            WeatherCache.objects.update_or_create(
                city_name=city_name,
                defaults={'weather_data': weather_info, 'cached_at': timezone.now()}
            )
        except Exception:
            pass

        return weather_info

    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.RequestException:
        return None
    except (KeyError, IndexError, ValueError):
        return None


def get_cached_weather_data(city_name):
    try:
        cached_weather = WeatherCache.objects.filter(city_name__iexact=city_name).first()
        if cached_weather and cached_weather.is_valid():
            data = cached_weather.weather_data
            data['cached'] = True
            return data
    except Exception:
        pass
    return None