from __future__ import annotations

import re
from typing import Any, Dict

import requests
from django.utils import timezone

from .. import config
from ..models import WeatherSnapshot


class WeatherServiceError(Exception):
    pass


_CITY_SANITIZE_PATTERN = re.compile(r"[^A-Za-zА-Яа-яЁё\-\s']")


def normalize_city(city: str) -> str:
    if not city:
        return ""
    cleaned = _CITY_SANITIZE_PATTERN.sub(" ", city.strip())
    parts = [part for part in cleaned.split() if part]
    if not parts:
        return ""
    normalized = " ".join(part.capitalize() for part in parts)
    return normalized[:128]


def get_weather(city: str) -> Dict[str, Any]:
    normalized = normalize_city(city)
    if not normalized:
        raise WeatherServiceError("Укажите город")

    snapshot = WeatherSnapshot.objects.filter(city__iexact=normalized).first()
    if snapshot and timezone.now() - snapshot.fetched_at < config.WEATHER_CACHE_DURATION:
        return snapshot.payload

    if not config.API_KEY:
        if snapshot:
            return snapshot.payload
        raise WeatherServiceError("Добавьте API-ключ OpenWeather в переменные окружения")

    params = {
        "q": normalized,
        "appid": config.API_KEY,
        "units": config.DEFAULT_WEATHER_UNITS,
        "lang": config.DEFAULT_WEATHER_LANG,
    }

    try:
        response = requests.get(config.API_BASE_URL, params=params, timeout=config.API_TIMEOUT)
    except requests.RequestException as exc:
        if snapshot:
            return snapshot.payload
        raise WeatherServiceError("Погодный сервис недоступен") from exc

    if response.status_code != 200:
        try:
            payload = response.json()
            message = payload.get("message") or "Не удалось получить данные"
        except ValueError:
            message = "Не удалось получить данные"
        if snapshot:
            return snapshot.payload
        raise WeatherServiceError(message.capitalize())

    try:
        payload = response.json()
    except ValueError as exc:
        if snapshot:
            return snapshot.payload
        raise WeatherServiceError("Получены некорректные данные погоды") from exc

    WeatherSnapshot.objects.update_or_create(
        city=normalized,
        defaults={"payload": payload, "fetched_at": timezone.now()},
    )
    return payload


def public_weather_payload(city: str, payload: Dict[str, Any], fetched_at=None) -> Dict[str, Any]:
    weather = (payload.get("weather") or [{}])[0]
    main = payload.get("main", {})
    wind = payload.get("wind", {})
    timestamp = fetched_at or timezone.now()

    return {
        "city": city,
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "description": weather.get("description"),
        "icon": weather.get("icon"),
        "wind_speed": wind.get("speed"),
        "fetched_at": timezone.localtime(timestamp).isoformat(),
        "raw": payload,
    }
