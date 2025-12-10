import requests
import json

def test_openweather_api():
    api_key = 'de0ba8afcd2606f2eccf6c212abe0906'
    
    # Тестируем для Москвы
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': 'Moscow',
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }
    
    print("🧪 Тестируем OpenWeatherMap API")
    print(f"🔗 URL: {url}")
    print(f"🔑 Ключ: {api_key}")
    print(f"🏙️  Город: Moscow")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ УСПЕХ! Данные получены:")
            print(f"🏙️  Город: {data['name']}, {data['sys']['country']}")
            print(f"🌡️  Температура: {data['main']['temp']}°C")
            print(f"🤔 Ощущается как: {data['main']['feels_like']}°C")
            print(f"💧 Влажность: {data['main']['humidity']}%")
            print(f"💨 Скорость ветра: {data['wind']['speed']} м/с")
            print(f"📊 Давление: {data['main']['pressure']} гПа")
            print(f"☁️  Состояние: {data['weather'][0]['description']}")
            print(f"🖼️  Иконка: {data['weather'][0]['icon']}")
            
            # Проверка URL иконки
            icon_url = f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
            print(f"🖼️  URL иконки: {icon_url}")
            
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            
    except Exception as e:
        print(f"💥 Исключение: {e}")

if __name__ == "__main__":
    test_openweather_api()