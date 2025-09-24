import requests
import os
from django.shortcuts import render

API_KEY = os.getenv("WEATHERBIT_API_KEY")

def index(request):
    weather_data = None
    error = None

    if request.method == "POST":
        city = request.POST.get("city")
        if city:
            url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={API_KEY}&lang=ru"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    info = data["data"][0]

                    # Определяем фон в зависимости от описания погоды
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
                    error = "Не удалось найти данные о погоде."
            else:
                error = "Ошибка при получении данных."
        else:
            error = "Введите название города."

    return render(request, "weather/index.html", {"weather": weather_data, "error": error})
