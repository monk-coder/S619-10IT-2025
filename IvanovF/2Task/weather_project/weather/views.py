import json
import os

import requests
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.utils.timezone import now

from datetime import timedelta

from .models import SearchHistory, WeatherTask, WeatherSnapshot

API_KEY_WEATHER = os.getenv("WEATHERBIT_API_KEY")
API_KEY_AVIA = os.getenv("AVIATIONSTACK_API_KEY")


def index(request):
    return render(request, "weather/index.html")


def get_weather(request):
    city = request.GET.get("city")
    if not city:
        return JsonResponse({"error": "Город не указан"}, status=400)

    city = city.strip()
    normalized = city.lower()

    snapshot = WeatherSnapshot.objects.filter(normalized_city=normalized).first()
    fresh_threshold = now() - timedelta(hours=2)
    use_cache = snapshot and snapshot.fetched_at >= fresh_threshold

    payload = None
    fetched_at = None
    from_cache = False

    if use_cache:
        payload = snapshot.payload
        fetched_at = snapshot.fetched_at
        from_cache = True
    else:
        url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={API_KEY_WEATHER}&lang=ru"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return JsonResponse({"error": f"Ошибка API погоды ({response.status_code})"}, status=500)
            data = response.json()
        except Exception as e:  # pragma: no cover - network issues
            return JsonResponse({"error": str(e)}, status=500)

        if "data" not in data or not data["data"]:
            return JsonResponse({"error": "Нет данных по городу"}, status=404)

        info = data["data"][0]
        payload = {
            "city": city,
            "temperature": info["temp"],
            "humidity": info["rh"],
            "description": info["weather"]["description"],
            "icon": f"https://www.weatherbit.io/static/img/icons/{info['weather']['icon']}.png",
        }

        if snapshot:
            snapshot.refresh(city, payload)
            fetched_at = snapshot.fetched_at
        else:
            snapshot = WeatherSnapshot.objects.create(
                city=city[:128],
                normalized_city=normalized[:128],
                payload=payload,
            )
            fetched_at = snapshot.fetched_at

    description = payload["description"].lower()
    if "ясн" in description:
        bg_class = "sunny"
    elif "дожд" in description:
        bg_class = "rainy"
    elif "снег" in description:
        bg_class = "snowy"
    elif "облач" in description:
        bg_class = "cloudy"
    else:
        bg_class = "default"

    if request.user.is_authenticated:
        SearchHistory.objects.create(
            user=request.user,
            city=city[:128],
        )

    return JsonResponse({
        **payload,
        "bg_class": bg_class,
        "cached": from_cache,
        "fetched_at": fetched_at.isoformat(),
    })


def get_time(request):
    """
    Получаем мировое время UTC с API (worldtimeapi.org).
    """
    try:
        resp = requests.get("https://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5)
        data = resp.json()
        # отдаем только нужные поля
        return JsonResponse({
            "utc_datetime": data.get("utc_datetime"),
            "unixtime": data.get("unixtime"),
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_flight(request):
    airport = request.GET.get("airport")
    if not airport:
        return JsonResponse({"error": "Аэропорт не указан"}, status=400)

    url = f"http://api.aviationstack.com/v1/flights?access_key={API_KEY_AVIA}&dep_iata={airport}&limit=1"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            flights = data.get("data", [])
            if flights:
                f = flights[0]
                return JsonResponse({
                    "flight_number": f["flight"]["iata"],
                    "airline": f["airline"]["name"],
                    "status": f["flight_status"],
                    "departure_airport": f["departure"]["airport"],
                    "arrival_airport": f["arrival"]["airport"],
                    "departure_time": f["departure"]["scheduled"],
                    "arrival_time": f["arrival"]["scheduled"],
                })
            return JsonResponse({"error": "Нет данных по этому аэропорту"}, status=404)
        return JsonResponse({"error": f"Ошибка API авиации ({response.status_code})"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Метод не поддерживается"}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return JsonResponse({"error": "Укажите логин и пароль"}, status=400)

    User = get_user_model()
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({"error": "Пользователь уже существует"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    login(request, user)
    return JsonResponse({
        "ok": True,
        "message": f"Пользователь {username} создан и авторизован",
        "username": username,
    })


@csrf_exempt
def login_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Метод не поддерживается"}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return JsonResponse({"error": "Укажите логин и пароль"}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"error": "Неверные учетные данные"}, status=400)

    login(request, user)
    return JsonResponse({
        "ok": True,
        "message": f"Добро пожаловать, {username}",
        "username": username,
    })


@csrf_exempt
def logout_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Метод не поддерживается"}, status=405)

    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({"ok": True, "message": "Вы вышли из системы"})

    return JsonResponse({"ok": True, "message": "Вы и так не авторизованы"})


def auth_status(request):
    if request.user.is_authenticated:
        return JsonResponse({"authenticated": True, "username": request.user.username})
    return JsonResponse({"authenticated": False})


@require_GET
def get_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({"entries": []})

    history = (
        SearchHistory.objects.filter(user=request.user)
        .order_by("-created_at")[:10]
    )
    payload = [
        {
            "city": item.city,
            "created_at": item.created_at.isoformat(),
        }
        for item in history
    ]
    return JsonResponse({"entries": payload})


def _serialize_task(task: WeatherTask) -> dict:
    return {
        "id": task.id,
        "city": task.city,
        "text": task.text,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


@csrf_exempt
def tasks_collection(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Требуется аутентификация"}, status=401)

    if request.method == "GET":
        tasks = WeatherTask.objects.filter(user=request.user).order_by("-created_at")
        return JsonResponse({"tasks": [_serialize_task(task) for task in tasks]})

    if request.method == "POST":
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Некорректный JSON"}, status=400)

        city = (payload.get("city") or "").strip()
        text = (payload.get("text") or "").strip()

        if not city or not text:
            return JsonResponse({"error": "Укажите город и текст напоминания"}, status=400)

        task = WeatherTask.objects.create(
            user=request.user,
            city=city[:128],
            text=text[:512],
        )
        return JsonResponse({"task": _serialize_task(task)}, status=201)

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)


@csrf_exempt
def task_detail(request, task_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Требуется аутентификация"}, status=401)

    try:
        task = WeatherTask.objects.get(id=task_id, user=request.user)
    except WeatherTask.DoesNotExist:
        return JsonResponse({"error": "Задача не найдена"}, status=404)

    if request.method == "GET":
        return JsonResponse({"task": _serialize_task(task)})

    if request.method in {"PUT", "PATCH"}:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Некорректный JSON"}, status=400)

        city = payload.get("city")
        text = payload.get("text")

        fields_to_update = []

        if city is not None:
            city = str(city).strip()
            if not city:
                return JsonResponse({"error": "Город не может быть пустым"}, status=400)
            task.city = city[:128]
            fields_to_update.append("city")

        if text is not None:
            text = str(text).strip()
            if not text:
                return JsonResponse({"error": "Текст не может быть пустым"}, status=400)
            task.text = text[:512]
            fields_to_update.append("text")

        if fields_to_update:
            fields_to_update.append("updated_at")
            task.save(update_fields=fields_to_update)
            task.refresh_from_db()

        return JsonResponse({"task": _serialize_task(task)})

    if request.method == "DELETE":
        task.delete()
        return JsonResponse({"ok": True})

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)
