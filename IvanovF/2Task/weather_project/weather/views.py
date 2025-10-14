import json
import os
from datetime import timedelta

import requests
from requests.exceptions import RequestException

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import SearchHistory, WeatherSnapshot, WeatherTask


def _get_config_value(settings_name, env_name, default=None):
    value = getattr(settings, settings_name, None)
    if value not in (None, ""):
        return value
    return os.getenv(env_name, default)


API_KEY_WEATHER = _get_config_value("WEATHERBIT_API_KEY", "WEATHERBIT_API_KEY")
API_URL_WEATHER = _get_config_value(
    "WEATHERBIT_API_URL",
    "WEATHERBIT_API_URL",
    "https://api.weatherbit.io/v2.0/current",
)
API_ICON_BASE_URL = _get_config_value(
    "WEATHERBIT_ICON_BASE_URL",
    "WEATHERBIT_ICON_BASE_URL",
    "https://www.weatherbit.io/static/img/icons/",
)
API_KEY_AVIA = _get_config_value("AVIATIONSTACK_API_KEY", "AVIATIONSTACK_API_KEY")
API_URL_AVIA = _get_config_value(
    "AVIATIONSTACK_API_URL",
    "AVIATIONSTACK_API_URL",
    "http://api.aviationstack.com/v1/flights",
)
API_KEY_CURRENCY = _get_config_value("FREECURRENCY_API_KEY", "FREECURRENCY_API_KEY")
API_URL_CURRENCY = _get_config_value(
    "FREECURRENCY_API_URL",
    "FREECURRENCY_API_URL",
    "https://api.freecurrencyapi.com/v1/latest",
)
API_URL_TIME = _get_config_value(
    "WORLDTIME_API_URL",
    "WORLDTIME_API_URL",
    "https://worldtimeapi.org/api/timezone/Etc/UTC",
)


BACKGROUND_KEYWORDS = (
    ("ясн", "sunny"),
    ("дожд", "rainy"),
    ("снег", "snowy"),
    ("облач", "cloudy"),
)

TASK_FIELD_LIMITS = {
    "city": 128,
    "text": 512,
}

EMPTY_FIELD_ERRORS = {
    "city": "Город не может быть пустым",
    "text": "Текст не может быть пустым",
}


def _json_error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _parse_json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("Некорректный JSON") from exc


def _determine_background(description):
    lowered = description.lower()
    for needle, css_class in BACKGROUND_KEYWORDS:
        if needle in lowered:
            return css_class
    return "default"


def index(request):
    return render(request, "weather/index.html")


@require_GET
def get_weather(request):
    if not API_KEY_WEATHER:
        return _json_error("API ключ погоды не настроен", status=500)

    city = (request.GET.get("city") or "").strip()
    if not city:
        return _json_error("Город не указан")

    normalized = city.lower()
    snapshot = WeatherSnapshot.objects.filter(normalized_city=normalized).first()
    fresh_threshold = timezone.now() - timedelta(hours=2)

    from_cache = False

    if snapshot and snapshot.fetched_at >= fresh_threshold:
        payload = snapshot.payload
        fetched_at = snapshot.fetched_at
        from_cache = True
    else:
        params = {
            "city": city,
            "key": API_KEY_WEATHER,
            "lang": "ru",
        }
        try:
            response = requests.get(API_URL_WEATHER, params=params, timeout=10)
        except RequestException as exc:  # pragma: no cover - сеть
            return _json_error(f"Ошибка соединения с API погоды: {exc}", status=500)

        if response.status_code != 200:
            return _json_error(f"Ошибка API погоды ({response.status_code})", status=500)

        try:
            data = response.json()
        except ValueError:
            return _json_error("Некорректный ответ API погоды", status=500)

        entries = data.get("data") or []
        if not entries:
            return _json_error("Нет данных по городу", status=404)

        info = entries[0]
        weather_info = info.get("weather") or {}
        icon_code = weather_info.get("icon")
        if not icon_code:
            return _json_error("Ответ API не содержит иконку погоды", status=500)

        icon_base = API_ICON_BASE_URL.rstrip("/")

        payload = {
            "city": city,
            "temperature": info.get("temp"),
            "humidity": info.get("rh"),
            "description": weather_info.get("description", ""),
            "icon": f"{icon_base}/{icon_code}.png",
        }

        fetched_at = timezone.now()
        WeatherSnapshot.objects.update_or_create(
            normalized_city=normalized[:128],
            defaults={
                "city": city[:128],
                "payload": payload,
                "fetched_at": fetched_at,
            },
        )

    bg_class = _determine_background(payload.get("description", ""))

    if request.user.is_authenticated:
        SearchHistory.objects.create(user=request.user, city=city[:128])

    return JsonResponse({
        **payload,
        "bg_class": bg_class,
        "cached": from_cache,
        "fetched_at": fetched_at.isoformat(),
    })


@require_GET
def get_time(request):
    try:
        response = requests.get(API_URL_TIME, timeout=5)
    except RequestException as exc:  # pragma: no cover - сеть
        return _json_error(f"Ошибка при запросе времени: {exc}", status=500)

    if response.status_code != 200:
        return _json_error(f"Ошибка API времени ({response.status_code})", status=500)

    try:
        data = response.json()
    except ValueError:
        return _json_error("Некорректный ответ API времени", status=500)

    return JsonResponse({
        "utc_datetime": data.get("utc_datetime"),
        "unixtime": data.get("unixtime"),
    })


@require_GET
def get_flight(request):
    if not API_KEY_AVIA:
        return _json_error("API ключ авиации не настроен", status=500)

    airport = (request.GET.get("airport") or "").strip().upper()
    if not airport:
        return _json_error("Аэропорт не указан")

    params = {
        "access_key": API_KEY_AVIA,
        "dep_iata": airport,
        "limit": 1,
    }

    try:
        response = requests.get(API_URL_AVIA, params=params, timeout=10)
    except RequestException as exc:  # pragma: no cover - сеть
        return _json_error(f"Ошибка соединения с API авиации: {exc}", status=500)

    if response.status_code != 200:
        return _json_error(f"Ошибка API авиации ({response.status_code})", status=500)

    try:
        data = response.json()
    except ValueError:
        return _json_error("Некорректный ответ API авиации", status=500)

    flights = data.get("data") or []
    if not flights:
        return _json_error("Нет данных по этому аэропорту", status=404)

    flight = flights[0]
    return JsonResponse({
        "flight_number": flight.get("flight", {}).get("iata"),
        "airline": flight.get("airline", {}).get("name"),
        "status": flight.get("flight_status"),
        "departure_airport": flight.get("departure", {}).get("airport"),
        "arrival_airport": flight.get("arrival", {}).get("airport"),
        "departure_time": flight.get("departure", {}).get("scheduled"),
        "arrival_time": flight.get("arrival", {}).get("scheduled"),
    })


@require_GET
def get_currency(request):
    if not API_KEY_CURRENCY:
        return _json_error("API ключ валюты не настроен", status=500)

    base = (request.GET.get("base") or "").strip().upper()
    symbols_raw = (request.GET.get("symbols") or "").strip().upper()

    if not base:
        return _json_error("Укажите базовую валюту")

    symbols = [symbol for symbol in symbols_raw.replace(";", ",").split(",") if symbol]
    if not symbols:
        return _json_error("Укажите валюты для конвертации")

    params = {
        "base_currency": base,
        "currencies": ",".join(symbols),
    }

    headers = {"apikey": API_KEY_CURRENCY}

    try:
        response = requests.get(API_URL_CURRENCY, params=params, headers=headers, timeout=10)
    except RequestException as exc:  # pragma: no cover - сеть
        return _json_error(f"Ошибка соединения с API валют: {exc}", status=500)

    if response.status_code != 200:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {}
        message = error_payload.get("message") or error_payload.get("error") or response.text
        return _json_error(f"Ошибка API валют ({response.status_code}): {message}", status=500)

    try:
        data = response.json()
    except ValueError:
        return _json_error("Некорректный ответ API валют", status=500)

    rates = data.get("data") or {}
    result = {code: rates.get(code) for code in symbols if code in rates}
    if not result:
        return _json_error("Не удалось получить курсы", status=404)

    return JsonResponse({
        "base": base,
        "rates": result,
        "fetched_at": timezone.now().isoformat(),
    })


@csrf_exempt
@require_POST
def register_user(request):
    try:
        payload = _parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return _json_error("Укажите логин и пароль")

    User = get_user_model()
    if User.objects.filter(username__iexact=username).exists():
        return _json_error("Пользователь уже существует")

    user = User.objects.create_user(username=username, password=password)
    login(request, user)
    return JsonResponse({
        "ok": True,
        "message": f"Пользователь {username} создан и авторизован",
        "username": username,
    })


@csrf_exempt
@require_POST
def login_user(request):
    try:
        payload = _parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return _json_error("Укажите логин и пароль")

    user = authenticate(request, username=username, password=password)
    if user is None:
        return _json_error("Неверные учетные данные")

    login(request, user)
    return JsonResponse({
        "ok": True,
        "message": f"Добро пожаловать, {username}",
        "username": username,
    })


@csrf_exempt
@require_POST
def logout_user(request):
    logged_in = request.user.is_authenticated
    logged_in and logout(request)
    message = "Вы вышли из системы" if logged_in else "Вы и так не авторизованы"
    return JsonResponse({"ok": True, "message": message})


@require_GET
def auth_status(request):
    return JsonResponse({
        "authenticated": request.user.is_authenticated,
        **({"username": request.user.username} if request.user.is_authenticated else {}),
    })


@require_GET
def get_history(request):
    history_qs = (
        SearchHistory.objects.filter(user=request.user)
        if request.user.is_authenticated
        else SearchHistory.objects.none()
    )
    history = history_qs.order_by("-created_at")[:10]
    entries = [
        {
            "city": item.city,
            "created_at": item.created_at.isoformat(),
        }
        for item in history
    ]
    return JsonResponse({"entries": entries})


def _serialize_task(task: WeatherTask) -> dict:
    return {
        "id": task.id,
        "city": task.city,
        "text": task.text,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _list_tasks(request):
    tasks = WeatherTask.objects.filter(user=request.user).order_by("-created_at")
    return JsonResponse({"tasks": [_serialize_task(task) for task in tasks]})


def _create_task(request):
    try:
        payload = _parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    normalized = {}
    for field, limit in TASK_FIELD_LIMITS.items():
        value = str(payload.get(field) or "").strip()
        if not value:
            return _json_error("Укажите город и текст напоминания")
        normalized[field] = value[:limit]

    task = WeatherTask.objects.create(user=request.user, **normalized)
    return JsonResponse({"task": _serialize_task(task)}, status=201)


def _task_get_handler(request, task):
    return JsonResponse({"task": _serialize_task(task)})


def _task_update_handler(request, task):
    try:
        payload = _parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    updates = {}
    for field, limit in TASK_FIELD_LIMITS.items():
        if field not in payload:
            continue
        value = str(payload.get(field) or "").strip()
        if not value:
            return _json_error(EMPTY_FIELD_ERRORS[field])
        updates[field] = value[:limit]

    if updates:
        for field, value in updates.items():
            setattr(task, field, value)
        task.save(update_fields=list(updates.keys()) + ["updated_at"])
        task.refresh_from_db()

    return JsonResponse({"task": _serialize_task(task)})


def _task_delete_handler(request, task):
    task.delete()
    return JsonResponse({"ok": True})


TASK_COLLECTION_HANDLERS = {
    "GET": _list_tasks,
    "POST": _create_task,
}


TASK_DETAIL_HANDLERS = {
    "GET": _task_get_handler,
    "PUT": _task_update_handler,
    "PATCH": _task_update_handler,
    "DELETE": _task_delete_handler,
}


@csrf_exempt
@require_http_methods(["GET", "POST"])
def tasks_collection(request):
    if not request.user.is_authenticated:
        return _json_error("Требуется аутентификация", status=401)

    handler = TASK_COLLECTION_HANDLERS[request.method]
    return handler(request)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def task_detail(request, task_id: int):
    if not request.user.is_authenticated:
        return _json_error("Требуется аутентификация", status=401)

    try:
        task = WeatherTask.objects.get(id=task_id, user=request.user)
    except WeatherTask.DoesNotExist:
        return _json_error("Задача не найдена", status=404)

    handler = TASK_DETAIL_HANDLERS[request.method]
    return handler(request, task)


@require_GET
def admin_overview(request):
    if not request.user.is_authenticated:
        return _json_error("Требуется аутентификация", status=401)
    if not request.user.is_staff:
        return _json_error("Недостаточно прав", status=403)

    User = get_user_model()

    users = (
        User.objects.annotate(
            tasks_count=Count("weather_tasks", distinct=True),
            searches_count=Count("weather_search_history", distinct=True),
        )
        .order_by("-date_joined")[:5]
    )

    users_payload = [
        {
            "username": user.username,
            "is_staff": bool(user.is_staff),
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "tasks_count": user.tasks_count,
            "searches_count": user.searches_count,
        }
        for user in users
    ]

    recent_tasks = [
        {
            "id": task.id,
            "user": task.user.username,
            "city": task.city,
            "text": task.text[:60],
            "created_at": task.created_at.isoformat(),
        }
        for task in WeatherTask.objects.select_related("user").order_by("-created_at")[:5]
    ]

    recent_searches = [
        {
            "user": history.user.username,
            "city": history.city,
            "created_at": history.created_at.isoformat(),
        }
        for history in SearchHistory.objects.select_related("user").order_by("-created_at")[:5]
    ]

    totals = {
        "users_total": User.objects.count(),
        "tasks_total": WeatherTask.objects.count(),
        "searches_total": SearchHistory.objects.count(),
    }

    return JsonResponse({
        "users": users_payload,
        "recent_tasks": recent_tasks,
        "recent_searches": recent_searches,
        "totals": totals,
    })
