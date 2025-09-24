import os
import requests
from django.conf import settings
from datetime import datetime


API_KEY = getattr(settings, 'OPENWEATHER_API_KEY', None)
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'


class OpenWeatherError(Exception):
    pass




def fetch_weather(city_name: str):
"""Запрос к OpenWeather. Возвращает dict с данными или кидает OpenWeatherError."""
    if not API_KEY:
        raise OpenWeatherError('API key not configured')


    params = {
    'q': city_name,
    'appid': API_KEY,
    'units': 'metric',
    'lang': 'ru'
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
    except requests.RequestException as e:
        raise OpenWeatherError(f'Network error: {e}')


    if r.status_code == 404:
      raise OpenWeatherError('Город не найден')
    if r.status_code == 401:
        raise OpenWeatherError('Неверный API ключ')
    if r.status_code != 200:
        raise OpenWeatherError(f'Ошибка API: {r.status_code}')


    data = r.json()
    # Собираем упрощённую структуру
    return {
    'city': data.get('name'),
    'temp': data['main']['temp'],
    'humidity': data['main']['humidity'],
    'desc': data['weather'][0]['description'],
    'icon': data['weather'][0]['icon'],
    'raw': data,
    'fetched_at': datetime.utcnow().isoformat() + 'Z'
    }