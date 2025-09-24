import os
import requests
from django.shortcuts import render

API_KEY_WEATHER = os.getenv("WEATHERBIT_API_KEY")
API_KEY_AVIA = os.getenv("AVIATIONSTACK_API_KEY")


def index(request):
    weather_data = None
    flight_data = None
    error_weather = None
    error_flight = None

    if request.method == "POST":
        # проверим какая форма отправлена
        if "city" in request.POST:  # погода
            city = request.POST.get("city")
            if city:
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

                            weather_data = {
                                "city": city,
                                "temperature": info["temp"],
                                "humidity": info["rh"],
                                "description": info["weather"]["description"],
                                "icon": f"https://www.weatherbit.io/static/img/icons/{info['weather']['icon']}.png",
                                "bg_class": bg_class,
                            }
                        else:
                            error_weather = "Не удалось найти данные о погоде."
                    else:
                        error_weather = f"Ошибка API погоды ({response.status_code})"
                except Exception as e:
                    error_weather = f"Ошибка при запросе погоды: {e}"
            else:
                error_weather = "Введите название города."

        elif "airport" in request.POST:  # самолёты
            airport = request.POST.get("airport")
            if airport:
                url = f"http://api.aviationstack.com/v1/flights?access_key={API_KEY_AVIA}&dep_iata={airport}&limit=1"
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        flights = data.get("data", [])
                        if flights:
                            f = flights[0]
                            flight_data = {
                                "flight_number": f["flight"]["iata"],
                                "airline": f["airline"]["name"],
                                "status": f["flight_status"],
                                "departure_airport": f["departure"]["airport"],
                                "arrival_airport": f["arrival"]["airport"],
                                "departure_time": f["departure"]["scheduled"],
                                "arrival_time": f["arrival"]["scheduled"],
                            }
                        else:
                            error_flight = "Нет данных по этому аэропорту."
                    else:
                        error_flight = f"Ошибка API авиации ({response.status_code})"
                except Exception as e:
                    error_flight = f"Ошибка при запросе авиации: {e}"
            else:
                error_flight = "Введите код аэропорта (IATA)."

    return render(
        request,
        "weather/index.html",
        {
            "weather": weather_data,
            "error_weather": error_weather,
            "flight": flight_data,
            "error_flight": error_flight,
        },
    )
