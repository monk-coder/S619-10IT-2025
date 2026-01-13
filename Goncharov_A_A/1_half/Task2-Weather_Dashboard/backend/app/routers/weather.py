import json
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_optional_user
from ..models import CachedWeather, CityHistory, User


router = APIRouter(prefix="/weather", tags=["weather"])
settings = get_settings()
CACHE_TTL = timedelta(hours=2)


@router.get("")
async def read_weather(
  request: Request,
  lat: float | None = None,
  lon: float | None = None,
  city: str | None = None,
  db: Session = Depends(get_db),
  current_user: User | None = Depends(get_optional_user)
):
  openweather_key = request.headers.get("X-Openweather-Key") or settings.openweather_key
  if not openweather_key:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenWeather API ключ не задан")

  cache_key = build_cache_key(lat=lat, lon=lon, city=city)
  if not cache_key:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Передайте координаты или название города")

  cached = db.query(CachedWeather).filter(CachedWeather.cache_key == cache_key).first()
  payload = None
  now = datetime.utcnow()

  if cached and cached.fetched_at >= now - CACHE_TTL:
    payload = json.loads(cached.payload)
  else:
    payload = await fetch_weather_from_api(openweather_key, lat=lat, lon=lon, city=city)
    if cached:
      cached.payload = json.dumps(payload)
      cached.fetched_at = now
    else:
      cached = CachedWeather(cache_key=cache_key, payload=json.dumps(payload), fetched_at=now)
      db.add(cached)

  if city and current_user:
    history = CityHistory(user_id=current_user.id, city=city.title(), searched_at=now)
    db.add(history)

  db.commit()
  return payload


def build_cache_key(*, lat: float | None, lon: float | None, city: str | None) -> str | None:
  if city:
    return f"city:{city.strip().lower()}"
  if lat is not None and lon is not None:
    return f"coord:{lat:.4f}:{lon:.4f}"
  return None


async def fetch_weather_from_api(api_key: str, *, lat: float | None, lon: float | None, city: str | None):
  params: dict[str, str] = {"appid": api_key, "units": "metric", "lang": "ru"}
  if city:
    params["q"] = city
  else:
    params["lat"] = str(lat)
    params["lon"] = str(lon)

  async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    if response.status_code != 200:
      raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"OpenWeather ответил кодом {response.status_code}"
      )
    return response.json()
