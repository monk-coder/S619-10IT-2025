from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import requests
import json
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-it-12345'

WEATHER_API_KEY = "16c1a5afa1e43f5176acc9e574baa9f3"

USERS_FILE = 'users_data.json'
RATINGS_FILE = 'ratings.json'


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_ratings():
    if os.path.exists(RATINGS_FILE):
        with open(RATINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'total_score': 0, 'total_votes': 0, 'user_votes': {}}


def save_ratings(ratings):
    with open(RATINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)


def get_user_stats(username):
    users = load_users()

    if username not in users:
        current_date = datetime.now().strftime('%d.%m.%Y')
        users[username] = {
            'password': None,
            'searches': 0,
            'cities': [],
            'favorite_city': None,
            'registration_date': current_date,
            'user_id': str(hash(username) % 10000 + 1000)
        }
        save_users(users)

    return users[username]


def update_user_search(username, city_name):
    users = load_users()

    if username not in users:
        current_date = datetime.now().strftime('%d.%m.%Y')
        users[username] = {
            'password': None,
            'searches': 0,
            'cities': [],
            'favorite_city': None,
            'registration_date': current_date,
            'user_id': str(hash(username) % 10000 + 1000)
        }

    users[username]['searches'] += 1

    city_lower = city_name.lower()
    existing_cities = [c.lower() for c in users[username]['cities']]
    if city_lower not in existing_cities:
        users[username]['cities'].append(city_name)

    save_users(users)


def get_happy_users_count():
    ratings = load_ratings()
    happy_count = 0
    for username, rating in ratings['user_votes'].items():
        if rating >= 4:
            happy_count += 1
    return happy_count


def get_weather(city_name):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&lang=ru&units=metric"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None, "Город не найден"

        data = response.json()

        pressure_mm = round(data['main']['pressure'] * 0.750064)

        weather_info = {
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'humidity': data['main']['humidity'],
            'pressure': pressure_mm,
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon']
        }
        return weather_info, None
    except requests.exceptions.Timeout:
        return None, "Превышено время ожидания"
    except Exception as e:
        return None, "Ошибка подключения"


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users = load_users()

        if username in users:
            if users[username].get('password') == hash_password(password):
                session['username'] = username
                return redirect(url_for('main_page', name=username))
            else:
                return render_template('login.html', error='Неверный пароль')
        else:
            return render_template('login.html', error='Пользователь не найден')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password:
            return render_template('register.html', error='Заполните все поля')

        if password != confirm_password:
            return render_template('register.html', error='Пароли не совпадают')

        if len(password) < 4:
            return render_template('register.html', error='Пароль должен быть не менее 4 символов')

        users = load_users()

        if username in users:
            return render_template('register.html', error='Пользователь уже существует')

        current_date = datetime.now().strftime('%d.%m.%Y')
        users[username] = {
            'password': hash_password(password),
            'searches': 0,
            'cities': [],
            'favorite_city': None,
            'registration_date': current_date,
            'user_id': str(hash(username) % 10000 + 1000)
        }
        save_users(users)

        session['username'] = username
        return redirect(url_for('main_page', name=username))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/main/<name>')
def main_page(name):
    if 'username' not in session or session['username'] != name:
        return redirect(url_for('login'))

    ratings = load_ratings()
    avg_rating = ratings['total_score'] / ratings['total_votes'] if ratings['total_votes'] > 0 else 0
    user_voted = name in ratings['user_votes']
    happy_users = get_happy_users_count()

    return render_template('main.html',
                           name=name,
                           avg_rating=avg_rating,
                           vote_count=ratings['total_votes'],
                           user_voted=user_voted,
                           happy_users=happy_users)


@app.route('/weather/<name>', methods=['GET', 'POST'])
def weather_page(name):
    if 'username' not in session or session['username'] != name:
        return redirect(url_for('login'))

    weather_data = None
    error_message = None
    city = None

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            weather_data, error_message = get_weather(city)
            if weather_data:
                update_user_search(name, city)

    return render_template('weather.html', name=name, weather=weather_data, error=error_message, city=city)


@app.route('/profile/<name>')
def profile_page(name):
    if 'username' not in session or session['username'] != name:
        return redirect(url_for('login'))

    user_stats = get_user_stats(name)
    ratings = load_ratings()
    user_rating = ratings['user_votes'].get(name)

    cities_count = len(user_stats.get('cities', []))
    favorite_city = user_stats.get('favorite_city')
    searches = user_stats.get('searches', 0)
    user_id = user_stats.get('user_id', str(hash(name) % 10000 + 1000))
    registration_date = user_stats.get('registration_date', datetime.now().strftime('%d.%m.%Y'))

    return render_template('profile.html',
                           name=name,
                           user_rating=user_rating,
                           searches=searches,
                           cities_visited=cities_count,
                           favorite_city=favorite_city,
                           user_id=user_id,
                           registration_date=registration_date)


@app.route('/get_favorite_weather/<name>')
def get_favorite_weather(name):
    if 'username' not in session or session['username'] != name:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    user_stats = get_user_stats(name)
    favorite_city = user_stats.get('favorite_city')

    if favorite_city:
        weather_data, error = get_weather(favorite_city)
        if weather_data:
            return jsonify({'success': True, 'weather': weather_data})
    return jsonify({'success': False})


@app.route('/rate', methods=['POST'])
def rate():
    data = request.get_json()
    username = data.get('username')
    rating = data.get('rating')

    if 'username' not in session or session['username'] != username:
        return jsonify({'error': 'Unauthorized'}), 401

    ratings = load_ratings()

    if username in ratings['user_votes']:
        return jsonify({'error': 'Already voted'}), 400

    ratings['total_score'] += rating
    ratings['total_votes'] += 1
    ratings['user_votes'][username] = rating

    save_ratings(ratings)

    new_avg = ratings['total_score'] / ratings['total_votes']
    happy_users = get_happy_users_count()

    return jsonify({
        'new_avg': new_avg,
        'new_count': ratings['total_votes'],
        'happy_users': happy_users
    })


@app.route('/update_favorite_city', methods=['POST'])
def update_favorite_city():
    data = request.get_json()
    username = data.get('username')
    city = data.get('city')

    if 'username' not in session or session['username'] != username:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    users = load_users()
    if username in users:
        users[username]['favorite_city'] = city
        save_users(users)
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


if __name__ == '__main__':
    app.run(debug=True)