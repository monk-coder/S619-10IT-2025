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


def get_iso_code(country_name):
    """Возвращает ISO код страны по её названию"""
    special_cases = {
        'Россия': 'ru', 'США': 'us', 'Германия': 'de', 'Франция': 'fr',
        'Япония': 'jp', 'Китай': 'cn', 'Великобритания': 'gb', 'Италия': 'it',
        'Бразилия': 'br', 'Канада': 'ca', 'Австралия': 'au', 'Индия': 'in',
        'Испания': 'es', 'Мексика': 'mx', 'Южная Корея': 'kr', 'Турция': 'tr',
        'Нидерланды': 'nl', 'Швеция': 'se', 'Норвегия': 'no', 'Финляндия': 'fi',
        'Дания': 'dk', 'Польша': 'pl', 'Украина': 'ua', 'Казахстан': 'kz',
        'Беларусь': 'by', 'Греция': 'gr', 'Португалия': 'pt', 'Бельгия': 'be',
        'Швейцария': 'ch', 'Австрия': 'at', 'Чехия': 'cz', 'Венгрия': 'hu',
        'Румыния': 'ro', 'Болгария': 'bg', 'Египет': 'eg', 'ЮАР': 'za',
        'Аргентина': 'ar', 'Чили': 'cl', 'Перу': 'pe', 'Колумбия': 'co',
        'Вьетнам': 'vn', 'Таиланд': 'th', 'Индонезия': 'id', 'Малайзия': 'my',
        'Филиппины': 'ph', 'Пакистан': 'pk', 'Нигерия': 'ng', 'Кения': 'ke',
        'Марокко': 'ma', 'Саудовская Аравия': 'sa', 'ОАЭ': 'ae', 'Израиль': 'il',
        'Сингапур': 'sg', 'Новая Зеландия': 'nz', 'Ирландия': 'ie', 'Исландия': 'is',
        'Хорватия': 'hr', 'Сербия': 'rs', 'Словакия': 'sk', 'Словения': 'si',
        'Эстония': 'ee', 'Латвия': 'lv', 'Литва': 'lt', 'Грузия': 'ge',
        'Армения': 'am', 'Азербайджан': 'az', 'Монголия': 'mn', 'Куба': 'cu',
        'Венесуэла': 've', 'Эквадор': 'ec', 'Боливия': 'bo', 'Парагвай': 'py',
        'Уругвай': 'uy', 'Коста-Рика': 'cr', 'Панама': 'pa', 'Доминикана': 'do',
        'Шри-Ланка': 'lk', 'Непал': 'np', 'Камбоджа': 'kh', 'Иран': 'ir',
        'Ирак': 'iq', 'Афганистан': 'af', 'Алжир': 'dz', 'Тунис': 'tn',
        'Ливия': 'ly', 'Судан': 'sd', 'Эфиопия': 'et', 'Гана': 'gh',
        'Ангола': 'ao', 'Мозамбик': 'mz'
    }

    if country_name in special_cases:
        return special_cases[country_name]
    return country_name[:2].lower()


def load_flags():
    if os.path.exists(FLAGS_FILE):
        with open(FLAGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    default_flags = {
        "countries": [
            {"name": "Россия", "flag": "🇷🇺", "iso_code": "ru"},
            {"name": "США", "flag": "🇺🇸", "iso_code": "us"},
            {"name": "Германия", "flag": "🇩🇪", "iso_code": "de"},
            {"name": "Франция", "flag": "🇫🇷", "iso_code": "fr"},
            {"name": "Япония", "flag": "🇯🇵", "iso_code": "jp"},
            {"name": "Китай", "flag": "🇨🇳", "iso_code": "cn"},
            {"name": "Великобритания", "flag": "🇬🇧", "iso_code": "gb"},
            {"name": "Италия", "flag": "🇮🇹", "iso_code": "it"},
            {"name": "Бразилия", "flag": "🇧🇷", "iso_code": "br"},
            {"name": "Канада", "flag": "🇨🇦", "iso_code": "ca"},
            {"name": "Австралия", "flag": "🇦🇺", "iso_code": "au"},
            {"name": "Индия", "flag": "🇮🇳", "iso_code": "in"},
            {"name": "Испания", "flag": "🇪🇸", "iso_code": "es"},
            {"name": "Мексика", "flag": "🇲🇽", "iso_code": "mx"},
            {"name": "Южная Корея", "flag": "🇰🇷", "iso_code": "kr"},
            {"name": "Турция", "flag": "🇹🇷", "iso_code": "tr"},
            {"name": "Нидерланды", "flag": "🇳🇱", "iso_code": "nl"},
            {"name": "Швеция", "flag": "🇸🇪", "iso_code": "se"},
            {"name": "Норвегия", "flag": "🇳🇴", "iso_code": "no"},
            {"name": "Финляндия", "flag": "🇫🇮", "iso_code": "fi"},
            {"name": "Дания", "flag": "🇩🇰", "iso_code": "dk"},
            {"name": "Польша", "flag": "🇵🇱", "iso_code": "pl"},
            {"name": "Украина", "flag": "🇺🇦", "iso_code": "ua"},
            {"name": "Казахстан", "flag": "🇰🇿", "iso_code": "kz"},
            {"name": "Беларусь", "flag": "🇧🇾", "iso_code": "by"},
            {"name": "Греция", "flag": "🇬🇷", "iso_code": "gr"},
            {"name": "Португалия", "flag": "🇵🇹", "iso_code": "pt"},
            {"name": "Бельгия", "flag": "🇧🇪", "iso_code": "be"},
            {"name": "Швейцария", "flag": "🇨🇭", "iso_code": "ch"},
            {"name": "Австрия", "flag": "🇦🇹", "iso_code": "at"},
            {"name": "Чехия", "flag": "🇨🇿", "iso_code": "cz"},
            {"name": "Венгрия", "flag": "🇭🇺", "iso_code": "hu"},
            {"name": "Румыния", "flag": "🇷🇴", "iso_code": "ro"},
            {"name": "Болгария", "flag": "🇧🇬", "iso_code": "bg"},
            {"name": "Египет", "flag": "🇪🇬", "iso_code": "eg"},
            {"name": "ЮАР", "flag": "🇿🇦", "iso_code": "za"},
            {"name": "Аргентина", "flag": "🇦🇷", "iso_code": "ar"},
            {"name": "Чили", "flag": "🇨🇱", "iso_code": "cl"},
            {"name": "Перу", "flag": "🇵🇪", "iso_code": "pe"},
            {"name": "Колумбия", "flag": "🇨🇴", "iso_code": "co"},
            {"name": "Вьетнам", "flag": "🇻🇳", "iso_code": "vn"},
            {"name": "Таиланд", "flag": "🇹🇭", "iso_code": "th"},
            {"name": "Индонезия", "flag": "🇮🇩", "iso_code": "id"},
            {"name": "Малайзия", "flag": "🇲🇾", "iso_code": "my"},
            {"name": "Филиппины", "flag": "🇵🇭", "iso_code": "ph"},
            {"name": "Пакистан", "flag": "🇵🇰", "iso_code": "pk"},
            {"name": "Нигерия", "flag": "🇳🇬", "iso_code": "ng"},
            {"name": "Кения", "flag": "🇰🇪", "iso_code": "ke"},
            {"name": "Марокко", "flag": "🇲🇦", "iso_code": "ma"},
            {"name": "Саудовская Аравия", "flag": "🇸🇦", "iso_code": "sa"},
            {"name": "ОАЭ", "flag": "🇦🇪", "iso_code": "ae"},
            {"name": "Израиль", "flag": "🇮🇱", "iso_code": "il"},
            {"name": "Сингапур", "flag": "🇸🇬", "iso_code": "sg"},
            {"name": "Новая Зеландия", "flag": "🇳🇿", "iso_code": "nz"},
            {"name": "Ирландия", "flag": "🇮🇪", "iso_code": "ie"},
            {"name": "Исландия", "flag": "🇮🇸", "iso_code": "is"},
            {"name": "Хорватия", "flag": "🇭🇷", "iso_code": "hr"},
            {"name": "Сербия", "flag": "🇷🇸", "iso_code": "rs"},
            {"name": "Словакия", "flag": "🇸🇰", "iso_code": "sk"},
            {"name": "Словения", "flag": "🇸🇮", "iso_code": "si"},
            {"name": "Эстония", "flag": "🇪🇪", "iso_code": "ee"},
            {"name": "Латвия", "flag": "🇱🇻", "iso_code": "lv"},
            {"name": "Литва", "flag": "🇱🇹", "iso_code": "lt"},
            {"name": "Грузия", "flag": "🇬🇪", "iso_code": "ge"},
            {"name": "Армения", "flag": "🇦🇲", "iso_code": "am"},
            {"name": "Азербайджан", "flag": "🇦🇿", "iso_code": "az"},
            {"name": "Монголия", "flag": "🇲🇳", "iso_code": "mn"},
            {"name": "Куба", "flag": "🇨🇺", "iso_code": "cu"},
            {"name": "Венесуэла", "flag": "🇻🇪", "iso_code": "ve"},
            {"name": "Эквадор", "flag": "🇪🇨", "iso_code": "ec"},
            {"name": "Боливия", "flag": "🇧🇴", "iso_code": "bo"},
            {"name": "Парагвай", "flag": "🇵🇾", "iso_code": "py"},
            {"name": "Уругвай", "flag": "🇺🇾", "iso_code": "uy"},
            {"name": "Коста-Рика", "flag": "🇨🇷", "iso_code": "cr"},
            {"name": "Панама", "flag": "🇵🇦", "iso_code": "pa"},
            {"name": "Доминикана", "flag": "🇩🇴", "iso_code": "do"},
            {"name": "Шри-Ланка", "flag": "🇱🇰", "iso_code": "lk"},
            {"name": "Непал", "flag": "🇳🇵", "iso_code": "np"},
            {"name": "Камбоджа", "flag": "🇰🇭", "iso_code": "kh"},
            {"name": "Иран", "flag": "🇮🇷", "iso_code": "ir"},
            {"name": "Ирак", "flag": "🇮🇶", "iso_code": "iq"},
            {"name": "Афганистан", "flag": "🇦🇫", "iso_code": "af"},
            {"name": "Алжир", "flag": "🇩🇿", "iso_code": "dz"},
            {"name": "Тунис", "flag": "🇹🇳", "iso_code": "tn"},
            {"name": "Ливия", "flag": "🇱🇾", "iso_code": "ly"},
            {"name": "Судан", "flag": "🇸🇩", "iso_code": "sd"},
            {"name": "Эфиопия", "flag": "🇪🇹", "iso_code": "et"},
            {"name": "Гана", "flag": "🇬🇭", "iso_code": "gh"},
            {"name": "Ангола", "flag": "🇦🇴", "iso_code": "ao"},
            {"name": "Мозамбик", "flag": "🇲🇿", "iso_code": "mz"}
        ]
    }
    save_flags(default_flags)
    return default_flags


def save_flags(flags):
    with open(FLAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(flags, f, ensure_ascii=False, indent=2)


def get_user_stats(username):
    users = load_users()
    today = datetime.now().strftime('%d.%m.%Y')

    if username not in users:
        users[username] = {
            'password': None,
            'searches': 0,
            'cities': [],
            'favorite_city': None,
            'registration_date': today,
            'user_id': str(hash(username) % 10000 + 1000),
            'coins': 0,
            'free_searches': 3,  # Бесплатные поиски (накапливаются)
            'last_daily_bonus': None,  # Дата последнего получения бонуса
            'game_score': 0
        }
        save_users(users)

    # Проверка на получение ежедневного бонуса
    if users[username].get('last_daily_bonus') != today:
        # Даём 3 бесплатных поиска каждый день
        users[username]['free_searches'] = users[username].get('free_searches', 0) + 3
        # Ограничиваем максимум 20 бесплатных поисков (чтобы не бесконечно копить)
        if users[username]['free_searches'] > 20:
            users[username]['free_searches'] = 20
        users[username]['last_daily_bonus'] = today
        save_users(users)

    return users[username]


def update_user_search(username, city_name):
    users = load_users()
    today = datetime.now().strftime('%d.%m.%Y')

    if username not in users:
        get_user_stats(username)  # Создаст пользователя с бонусом
        users = load_users()

    # Проверяем обновление бонуса
    if users[username].get('last_daily_bonus') != today:
        users[username]['free_searches'] = users[username].get('free_searches', 0) + 3
        if users[username]['free_searches'] > 20:
            users[username]['free_searches'] = 20
        users[username]['last_daily_bonus'] = today

    # Увеличиваем общее количество поисков (безлимитно)
    users[username]['searches'] = users[username].get('searches', 0) + 1

    # Тратим бесплатный поиск, если они есть
    free_searches = users[username].get('free_searches', 0)
    if free_searches > 0:
        users[username]['free_searches'] = free_searches - 1

    # Добавляем город в список посещённых
    city_lower = city_name.lower()
    existing_cities = [c.lower() for c in users[username].get('cities', [])]
    if city_lower not in existing_cities:
        users[username]['cities'].append(city_name)

    save_users(users)


def get_available_searches(username):
    """Возвращает количество доступных бесплатных поисков"""
    users = load_users()
    if username in users:
        return users[username].get('free_searches', 0)
    return 3


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


def get_top_players(limit=10):
    users = load_users()
    players = []

    for username, data in users.items():
        if data.get('password') is not None:
            players.append({
                'username': username,
                'coins': data.get('coins', 0),
                'game_score': data.get('game_score', 0),
                'searches': data.get('searches', 0)
            })

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
            'free_searches': 3,
            'last_daily_bonus': current_date,
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
    available_searches = get_available_searches(name)
    top_players = get_top_players(5)

    return render_template('main.html',
                           name=name,
                           avg_rating=avg_rating,
                           vote_count=ratings['total_votes'],
                           user_voted=user_voted,
                           happy_users=happy_users,
                           coins=coins,
                           available_searches=available_searches,
                           top_players=top_players)


@app.route('/weather/<name>', methods=['GET', 'POST'])
def weather_page(name):
    if 'username' not in session or session['username'] != name:
        return redirect(url_for('login'))

    weather_data = None
    error_message = None
    city = None
    search_error = None
    available_searches = get_available_searches(name)
    user_stats = get_user_stats(name)
    coins = user_stats.get('coins', 0)

    if request.method == 'POST':
        city = request.form.get('city')
        if available_searches <= 0:
            search_error = f"У вас закончились бесплатные поиски! Купите дополнительные поиски за монеты в игре или подождите завтрашнего бонуса. У вас {coins} 🪙"
        elif city:
            weather_data, error_message = get_weather(city)
            if weather_data:
                update_user_search(name, city)
                available_searches = get_available_searches(name)

    return render_template('weather.html',
                           name=name,
                           weather=weather_data,
                           error=error_message,
                           city=city,
                           available_searches=available_searches,
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
    free_searches = user_stats.get('free_searches', 0)

    return render_template('profile.html',
                           name=name,
                           user_rating=user_rating,
                           searches=searches,
                           cities_visited=cities_count,
                           favorite_city=favorite_city,
                           user_id=user_id,
                           registration_date=registration_date,
                           coins=coins,
                           game_score=game_score,
                           free_searches=free_searches)


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
    flags = load_flags()
    countries = flags['countries']

    correct_country = random.choice(countries)
    other_countries = [c for c in countries if c['name'] != correct_country['name']]
    wrong_answers = random.sample(other_countries, 3)

    options = [correct_country['name']] + [w['name'] for w in wrong_answers]
    random.shuffle(options)

    return jsonify({
        'success': True,
        'flag_emoji': correct_country['flag'],
        'flag_iso': correct_country.get('iso_code', get_iso_code(correct_country['name'])),
        'options': options,
        'correct': correct_country['name']
    })


@app.route('/check_answer', methods=['POST'])
def check_answer():
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
        coins_earned = 10
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
        coins_earned = 0
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
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Проверяем наличие бесплатных поисков
    free_searches = users[username].get('free_searches', 0)

    if free_searches <= 0:
        return jsonify({
            'success': False,
            'error': 'Недостаточно поисков! Сыграйте в игру или подождите завтрашнего бонуса.'
        }), 400

    # Тратим 1 поиск на смену города
    users[username]['free_searches'] = free_searches - 1
    users[username]['favorite_city'] = city
    # Увеличиваем счётчик общих поисков (опционально)
    users[username]['searches'] = users[username].get('searches', 0) + 1

    save_users(users)

    return jsonify({
        'success': True,
        'new_available': users[username]['free_searches'],
        'message': f'Любимый город изменён на {city}! Осталось {users[username]["free_searches"]} поисков.'
    })


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

    SEARCH_COST = 100
    SEARCHES_TO_ADD = 1
    user_coins = users[username].get('coins', 0)

    if user_coins >= SEARCH_COST:
        users[username]['coins'] = user_coins - SEARCH_COST
        users[username]['free_searches'] = users[username].get('free_searches', 0) + SEARCHES_TO_ADD
        # Ограничиваем максимум 20 бесплатных поисков
        if users[username]['free_searches'] > 20:
            users[username]['free_searches'] = 20
        save_users(users)
        return jsonify({
            'success': True,
            'new_coins': users[username]['coins'],
            'new_available': users[username]['free_searches']
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Недостаточно монет! Нужно {SEARCH_COST} 🪙, у вас {user_coins}'
        }), 400


@app.route('/claim_daily_bonus', methods=['POST'])
def claim_daily_bonus():
    """Получить ежедневный бонус (3 бесплатных поиска)"""
    data = request.get_json()
    username = data.get('username')

    if 'username' not in session or session['username'] != username:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    users = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    today = datetime.now().strftime('%d.%m.%Y')
    last_bonus = users[username].get('last_daily_bonus')

    if last_bonus == today:
        return jsonify({
            'success': False,
            'error': 'Вы уже получили сегодняшний бонус! Возвращайтесь завтра.'
        }), 400

    # Даём бонус
    users[username]['free_searches'] = users[username].get('free_searches', 0) + 3
    if users[username]['free_searches'] > 20:
        users[username]['free_searches'] = 20
    users[username]['last_daily_bonus'] = today
    save_users(users)

    return jsonify({
        'success': True,
        'new_available': users[username]['free_searches'],
        'message': '+3 бесплатных поиска!'
    })


if __name__ == '__main__':
    app.run(debug=True)