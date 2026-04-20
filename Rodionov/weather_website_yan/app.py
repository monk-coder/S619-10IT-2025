from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

WEATHER_API_KEY = "16c1a5afa1e43f5176acc9e574baa9f3"

def get_weather(city_name):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&lang=ru"
        response = requests.get(url)

        if response.status_code != 200:
            return None, "Город не найден"

        data = response.json()
        weather_info = {
            'temp': round(data['main']['temp'] - 273.15, 1),
            'feels_like': round(data['main']['feels_like'] - 273.15, 1),
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description']
        }
        return weather_info, None
    except Exception as e:
        return None, "Ошибка подключения"


@app.route('/', methods=['GET', 'POST'])
def enter_name():
    if request.method == 'POST':
        name = request.form.get('username')
        return redirect(url_for('main_page', name=name))
    return render_template('name.html')


@app.route('/main/<name>')
def main_page(name):
    return render_template('main.html', name=name)


@app.route('/weather/<name>', methods=['GET', 'POST'])
def weather_page(name):
    weather_data = None
    error_message = None
    city = None

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            weather_data, error_message = get_weather(city)

    return render_template('weather.html', name=name, weather=weather_data, error=error_message, city=city)


if __name__ == '__main__':
    app.run(debug=True)