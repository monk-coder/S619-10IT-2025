from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import requests
import json
import os
from datetime import datetime
import hashlib
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-it-12345'

WEATHER_API_KEY = "16c1a5afa1e43f5176acc9e574baa9f3"

USERS_FILE = 'users_data.json'
RATINGS_FILE = 'ratings.json'
FLAGS_FILE = 'flags_data.json'


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


def load_flags():
    """Загрузка базы флагов с реальными эмодзи"""
    if os.path.exists(FLAGS_FILE):
        with open(FLAGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    # База флагов с реальными эмодзи флагов
    default_flags = {
        "countries": [
            {"name": "Россия", "flag": "🇷🇺"},
            {"name": "США", "flag": "🇺🇸"},
            {"name": "Германия", "flag": "🇩🇪"},
            {"name": "Франция", "flag": "🇫🇷"},
            {"name": "Япония", "flag": "🇯🇵"},
            {"name": "Китай", "flag": "🇨🇳"},
            {"name": "Великобритания", "flag": "🇬🇧"},
            {"name": "Италия", "flag": "🇮🇹"},
            {"name": "Бразилия", "flag": "🇧🇷"},
            {"name": "Канада", "flag": "🇨🇦"},
            {"name": "Австралия", "flag": "🇦🇺"},
            {"name": "Индия", "flag": "🇮🇳"},
            {"name": "Испания", "flag": "🇪🇸"},
            {"name": "Мексика", "flag": "🇲🇽"},
            {"name": "Южная Корея", "flag": "🇰🇷"},
            {"name": "Турция", "flag": "🇹🇷"},
            {"name": "Нидерланды", "flag": "🇳🇱"},
            {"name": "Швеция", "flag": "🇸🇪"},
            {"name": "Норвегия", "flag": "🇳🇴"},
            {"name": "Финляндия", "flag": "🇫🇮"},
            {"name": "Дания", "flag": "🇩🇰"},
            {"name": "Польша", "flag": "🇵🇱"},
            {"name": "Украина", "flag": "🇺🇦"},
            {"name": "Казахстан", "flag": "🇰🇿"},
            {"name": "Беларусь", "flag": "🇧🇾"},
            {"name": "Греция", "flag": "🇬🇷"},
            {"name": "Португалия", "flag": "🇵🇹"},
            {"name": "Бельгия", "flag": "🇧🇪"},
            {"name": "Швейцария", "flag": "🇨🇭"},
            {"name": "Австрия", "flag": "🇦🇹"},
            {"name": "Чехия", "flag": "🇨🇿"},
            {"name": "Венгрия", "flag": "🇭🇺"},
            {"name": "Румыния", "flag": "🇷🇴"},
            {"name": "Болгария", "flag": "🇧🇬"},
            {"name": "Египет", "flag": "🇪🇬"},
            {"name": "ЮАР", "flag": "🇿🇦"},
            {"name": "Аргентина", "flag": "🇦🇷"},
            {"name": "Чили", "flag": "🇨🇱"},
            {"name": "Перу", "flag": "🇵🇪"},
            {"name": "Колумбия", "flag": "🇨🇴"},
            {"name": "Вьетнам", "flag": "🇻🇳"},
            {"name": "Таиланд", "flag": "🇹🇭"},
            {"name": "Индонезия", "flag": "🇮🇩"},
            {"name": "Малайзия", "flag": "🇲🇾"},
            {"name": "Филиппины", "flag": "🇵🇭"},
            {"name": "Пакистан", "flag": "🇵🇰"},
            {"name": "Нигерия", "flag": "🇳🇬"},
            {"name": "Кения", "flag": "🇰🇪"},
            {"name": "Марокко", "flag": "🇲🇦"},
            {"name": "Саудовская Аравия", "flag": "🇸🇦"},
            {"name": "ОАЭ", "flag": "🇦🇪"},
            {"name": "Израиль", "flag": "🇮🇱"},
            {"name": "Сингапур", "flag": "🇸🇬"},
            {"name": "Новая Зеландия", "flag": "🇳🇿"},
            {"name": "Ирландия", "flag": "🇮🇪"},
            {"name": "Исландия", "flag": "🇮🇸"},
            {"name": "Хорватия", "flag": "🇭🇷"},
            {"name": "Сербия", "flag": "🇷🇸"},
            {"name": "Словакия", "flag": "🇸🇰"},
            {"name": "Словения", "flag": "🇸🇮"},
            {"name": "Эстония", "flag": "🇪🇪"},
            {"name": "Латвия", "flag": "🇱🇻"},
            {"name": "Литва", "flag": "🇱🇹"},
            {"name": "Грузия", "flag": "🇬🇪"},
            {"name": "Армения", "flag": "🇦🇲"},
            {"name": "Азербайджан", "flag": "🇦🇿"},
            {"name": "Монголия", "flag": "🇲🇳"},
            {"name": "Куба", "flag": "🇨🇺"},
            {"name": "Венесуэла", "flag": "🇻🇪"},
            {"name": "Эквадор", "flag": "🇪🇨"},
            {"name": "Боливия", "flag": "🇧🇴"},
            {"name": "Парагвай", "flag": "🇵🇾"},
            {"name": "Уругвай", "flag": "🇺🇾"},
            {"name": "Коста-Рика", "flag": "🇨🇷"},
            {"name": "Панама", "flag": "🇵🇦"},
            {"name": "Доминикана", "flag": "🇩🇴"},
            {"name": "Шри-Ланка", "flag": "🇱🇰"},
            {"name": "Непал", "flag": "🇳🇵"},
            {"name": "Камбоджа", "flag": "🇰🇭"},
            {"name": "Иран", "flag": "🇮🇷"},
            {"name": "Ирак", "flag": "🇮🇶"},
            {"name": "Афганистан", "flag": "🇦🇫"},
            {"name": "Алжир", "flag": "🇩🇿"},
            {"name": "Тунис", "flag": "🇹🇳"},
            {"name": "Ливия", "flag": "🇱🇾"},
            {"name": "Судан", "flag": "🇸🇩"},
            {"name": "Эфиопия", "flag": "🇪🇹"},
            {"name": "Гана", "flag": "🇬🇭"},
            {"name": "Ангола", "flag": "🇦🇴"},
            {"name": "Мозамбик", "flag": "🇲🇿"}
        ]
    }
    save_flags(default_flags)
    return default_flags


def save_flags(flags):
    with open(FLAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(flags, f, ensure_ascii=False, indent=2)


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
            'user_id': str(hash(username) % 10000 + 1000),
            'coins': 0,
            'daily_searches': 0,
            'last_search_date': current_date,
            'game_score': 0
        }
        save_users(users)

    # Проверка на смену дня для обновления daily_searches
    today = datetime.now().strftime('%d.%m.%Y')
    if users[username].get('last_search_date') != today:
        users[username]['daily_searches'] = 0
        users[username]['last_search_date'] = today
        save_users(users)

    return users[username]


def update_user_search(username, city_name):
    users = load_users()
    today = datetime.now().strftime('%d.%m.%Y')

    if username not in users:
        current_date = datetime.now().strftime('%d.%m.%Y')
        users[username] = {
            'password': None,
            'searches': 0,
            'cities': [],
            'favorite_city': None,
            'registration_date': current_date,
            'user_id': str(hash(username) % 10000 + 1000),
            'coins': 0,
            'daily_searches': 0,
            'last_search_date': current_date,
            'game_score': 0
        }

    if users[username].get('last_search_date') != today:
        users[username]['daily_searches'] = 0
        users[username]['last_search_date'] = today

    users[username]['searches'] += 1
    users[username]['daily_searches'] += 1

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


def get_remaining_searches(username):
    """Возвращает оставшееся количество бесплатных поисков на сегодня"""
    users = load_users()
    if username in users:
        daily_searches = users[username].get('daily_searches', 0)
        return max(0, 3 - daily_searches)
    return 3


def get_top_players(limit=10):
    """Получить топ игроков по количеству монет и правильных ответов"""
    users = load_users()
    players = []

    for username, data in users.items():
        if data.get('password') is not None:  # Только зарегистрированные пользователи
            players.append({
                'username': username,
                'coins': data.get('coins', 0),
                'game_score': data.get('game_score', 0),
                'searches': data.get('searches', 0)
            })

    # Сортируем по количеству правильных ответов (game_score)
    players.sort(key=lambda x: x['game_score'], reverse=True)
    return players[:limit]


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

        if len(password) < 8:
            return render_template('register.html', error='Пароль должен быть не менее 8 символов')

        strength = 0
        if len(password) >= 8:
            strength += 1
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(not c.isalnum() for c in password):
            strength += 1

        if strength < 3:
            return render_template('register.html',
                                   error='Пароль слишком простой. Используйте заглавные буквы, цифры или спецсимволы')

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
            'user_id': str(hash(username) % 10000 + 1000),
            'coins': 0,
            'daily_searches': 0,
            'last_search_date': current_date,
            'game_score': 0
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
    user_stats = get_user_stats(name)
    coins = user_stats.get('coins', 0)
    remaining_searches = get_remaining_searches(name)
    top_players = get_top_players(5)

    return render_template('main.html',
                           name=name,
                           avg_rating=avg_rating,
                           vote_count=ratings['total_votes'],
                           user_voted=user_voted,
                           happy_users=happy_users,
                           coins=coins,
                           remaining_searches=remaining_searches,
                           top_players=top_players)


@app.route('/weather/<name>', methods=['GET', 'POST'])
def weather_page(name):
    if 'username' not in session or session['username'] != name:
        return redirect(url_for('login'))

    weather_data = None
    error_message = None
    city = None
    search_error = None
    remaining_searches = get_remaining_searches(name)
    user_stats = get_user_stats(name)
    coins = user_stats.get('coins', 0)

    if request.method == 'POST':
        city = request.form.get('city')
        if remaining_searches <= 0 and user_stats.get('daily_searches', 0) >= 3:
            search_error = f"У вас закончились бесплатные поиски на сегодня! Купите дополнительные поиски за монеты в игре. У вас {coins} 🪙"
        elif city:
            weather_data, error_message = get_weather(city)
            if weather_data:
                update_user_search(name, city)
                remaining_searches = get_remaining_searches(name)

    return render_template('weather.html',
                           name=name,
                           weather=weather_data,
                           error=error_message,
                           city=city,
                           remaining_searches=remaining_searches,
                           coins=coins,
                           search_error=search_error)


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
    coins = user_stats.get('coins', 0)
    game_score = user_stats.get('game_score', 0)

    return render_template('profile.html',
                           name=name,
                           user_rating=user_rating,
                           searches=searches,
                           cities_visited=cities_count,
                           favorite_city=favorite_city,
                           user_id=user_id,
                           registration_date=registration_date,
                           coins=coins,
                           game_score=game_score)


@app.route('/game/<name>')
def game_page(name):
    if 'username' not in session or session['username'] != name:
        return redirect(url_for('login'))

    user_stats = get_user_stats(name)
    coins = user_stats.get('coins', 0)
    game_score = user_stats.get('game_score', 0)
    top_players = get_top_players(10)

    return render_template('game.html',
                           name=name,
                           coins=coins,
                           game_score=game_score,
                           top_players=top_players)


@app.route('/get_question')
def get_question():
    """Получить случайный вопрос для игры с реальными флагами"""
    flags = load_flags()
    countries = flags['countries']

    # Выбираем случайную страну
    correct_country = random.choice(countries)

    # Выбираем 3 случайных неправильных ответа
    other_countries = [c for c in countries if c['name'] != correct_country['name']]
    wrong_answers = random.sample(other_countries, 3)

    options = [correct_country['name']] + [w['name'] for w in wrong_answers]
    random.shuffle(options)

    return jsonify({
        'success': True,
        'flag_emoji': correct_country['flag'],
        'options': options,
        'correct': correct_country['name']
    })


@app.route('/check_answer', methods=['POST'])
def check_answer():
    """Проверить ответ и начислить монеты"""
    data = request.get_json()
    username = data.get('username')
    selected = data.get('selected')
    correct = data.get('correct')

    if 'username' not in session or session['username'] != username:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    users = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    is_correct = (selected == correct)

    if is_correct:
        coins_earned = random.randint(5, 15)
        users[username]['coins'] = users[username].get('coins', 0) + coins_earned
        users[username]['game_score'] = users[username].get('game_score', 0) + 1
        save_users(users)
        return jsonify({
            'success': True,
            'is_correct': True,
            'coins_earned': coins_earned,
            'new_coins': users[username]['coins'],
            'new_score': users[username]['game_score']
        })
    else:
        coins_earned = random.randint(1, 3)
        users[username]['coins'] = users[username].get('coins', 0) + coins_earned
        save_users(users)
        return jsonify({
            'success': True,
            'is_correct': False,
            'correct_answer': correct,
            'coins_earned': coins_earned,
            'new_coins': users[username]['coins'],
            'new_score': users[username]['game_score']
        })


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


@app.route('/buy_searches', methods=['POST'])
def buy_searches():
    """Купить дополнительные поиски за монеты"""
    data = request.get_json()
    username = data.get('username')

    if 'username' not in session or session['username'] != username:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    users = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    SEARCH_COST = 5
    user_coins = users[username].get('coins', 0)

    if user_coins >= SEARCH_COST:
        users[username]['coins'] = user_coins - SEARCH_COST
        users[username]['daily_searches'] = max(0, users[username].get('daily_searches', 0) - 1)
        save_users(users)
        return jsonify({
            'success': True,
            'new_coins': users[username]['coins'],
            'new_remaining': max(0, 3 - users[username]['daily_searches'])
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Недостаточно монет! Нужно {SEARCH_COST} 🪙, у вас {user_coins}'
        }), 400


if __name__ == '__main__':
    app.run(debug=True)