import requests
from django.shortcuts import render

# Вставь сюда свой API-ключ с weatherbit.io
API_KEY = "cюдаключ"

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
                    weather_data = {
                        "city": city,
                        "temperature": data["data"][0]["temp"],
                        "description": data["data"][0]["weather"]["description"],
                    }
                else:
                    error = "Не удалось найти данные о погоде."
            else:
                error = "Ошибка при получении данных."
        else:
            error = "Введите название города."

    return render(request, "weather/index.html", {"weather": weather_data, "error": error})
