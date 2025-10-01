import os
import requests
from django.http import JsonResponse
from django.shortcuts import render

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
