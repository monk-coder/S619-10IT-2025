import json
import os

import requests
from django.contrib.auth import authenticate, get_user_model, login
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .models import SearchHistory

API_KEY_WEATHER = os.getenv("WEATHERBIT_API_KEY")
API_KEY_AVIA = os.getenv("AVIATIONSTACK_API_KEY")


def index(request):
    return render(request, "weather/index.html")


def get_weather(request):
    city = request.GET.get("city")
    if not city:
        return JsonResponse({"error": "Город не указан"}, status=400)

    url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={API_KEY_WEATHER}&lang=ru"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]:
                info = data["data"][0]
                description = info["weather"]["description"].lower()
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
                        city=city.strip()[:128],
                    )

                return JsonResponse({
                    "city": city,
                    "temperature": info["temp"],
                    "humidity": info["rh"],
                    "description": info["weather"]["description"],
                    "icon": f"https://www.weatherbit.io/static/img/icons/{info['weather']['icon']}.png",
                    "bg_class": bg_class,
                })
            return JsonResponse({"error": "Нет данных по городу"}, status=404)
        return JsonResponse({"error": f"Ошибка API погоды ({response.status_code})"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

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
