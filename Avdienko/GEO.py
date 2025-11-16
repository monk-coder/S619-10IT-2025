import os
import json
from flask import Flask, render_template_string, url_for, flash, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secure-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///georgia_cities.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    favorite_city = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Данные о городах Грузии с градиентами
def get_cities_data():
    return {
        "Тбилиси": {
            "description": "Столица и крупнейший город Грузии, расположенный на берегу реки Куры. Известен своими серными банями, старым городом и богатой историей.",
            "population": "1,184,818",
            "area": "726 км²",
            "average_salary": "1,200-2,200 GEL",
            "specialty": "Столица, культурный и экономический центр",
            "climate": "Умеренный, 13°C среднегодовая",
            "color": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "icon": "🏛️",
            "attractions": ["Старый город", "Крепость Нарикала", "Собор Цминда Самеба", "Мост Мира"],
            "cuisine": ["Хинкали", "Хачапури", "Сациви", "Купаты"],
            "foundation": "V век н.э.",
            "coordinates": "41.7151° N, 44.8271° E"
        },
        "Батуми": {
            "description": "Современный курортный город на черноморском побережье, известный своей архитектурой, ботаническим садом и канатной дорогой.",
            "population": "172,100",
            "area": "64.9 км²",
            "average_salary": "1,000-1,800 GEL",
            "specialty": "Морской курорт и туристический центр",
            "climate": "Субтропический, 14°C среднегодовая",
            "color": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "icon": "🌊",
            "attractions": ["Батумский бульвар", "Ботанический сад", "Площадь Европы", "Алфавитная башня"],
            "cuisine": ["Аджарское хачапури", "Морская рыба", "Чурчхела"],
            "foundation": "VIII век до н.э.",
            "coordinates": "41.6458° N, 41.6417° E"
        },
        "Кутаиси": {
            "description": "Второй по величине город Грузии, древняя столица Колхидского царства с богатым историческим наследием.",
            "population": "147,900",
            "area": "67.7 км²",
            "average_salary": "800-1,500 GEL",
            "specialty": "Исторический и промышленный центр",
            "climate": "Влажный субтропический, 14.5°C",
            "color": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
            "icon": "⛪",
            "attractions": ["Собор Баграта", "Гелатский монастырь", "Пещера Прометея"],
            "cuisine": ["Имеретинское хачапури", "Эларджи", "Гоми"],
            "foundation": "VI век до н.э.",
            "coordinates": "42.25° N, 42.7° E"
        },
        "Боржоми": {
            "description": "Курортный город в ущелье реки Куры, всемирно известный своими минеральными источниками и национальным парком.",
            "population": "13,800",
            "area": "16.7 км²",
            "average_salary": "700-1,300 GEL",
            "specialty": "Бальнеологический курорт",
            "climate": "Умеренный горный, 10°C",
            "color": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
            "icon": "💧",
            "attractions": ["Боржомское ущелье", "Национальный парк", "Минеральные источники"],
            "cuisine": ["Боржоми (вода)", "Шашлык", "Пхали"],
            "foundation": "XIX век",
            "coordinates": "41.8392° N, 43.3922° E"
        }
    }


# Базовый HTML шаблон
base_html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discover Georgia - Официальный гид</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #da291c;
            --secondary: #ffffff;
            --accent: #ffd700;
            --dark: #2c3e50;
            --light: #f8f9fa;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: #f8f9fa;
            min-height: 100vh;
        }

        .navbar {
            background: var(--dark) !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .hero-section {
            background: linear-gradient(135deg, var(--primary) 0%, #b3241a 100%);
            color: white;
            padding: 100px 0;
            position: relative;
            overflow: hidden;
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 100" fill="%23ffffff20"><polygon points="0,0 1000,100 1000,0"/></svg>');
            background-size: cover;
        }

        .card {
            border: none;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            overflow: hidden;
            background: white;
        }

        .card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }

        .city-card {
            height: 100%;
        }

        .city-header {
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            position: relative;
            overflow: hidden;
        }

        .city-icon {
            font-size: 4rem;
            filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3));
            z-index: 2;
        }

        .city-badge {
            background: var(--primary);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            position: absolute;
            top: 15px;
            right: 15px;
            z-index: 3;
        }

        .stat-card {
            text-align: center;
            padding: 30px 20px;
            border-radius: 15px;
            background: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-icon {
            font-size: 3rem;
            margin-bottom: 15px;
            color: var(--primary);
        }

        .section-title {
            position: relative;
            padding-bottom: 15px;
            margin-bottom: 40px;
            text-align: center;
            color: var(--dark);
            font-weight: 700;
        }

        .section-title::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 4px;
            background: var(--primary);
            border-radius: 2px;
        }

        .btn-primary {
            background: var(--primary);
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            background: #b3241a;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(218, 41, 28, 0.3);
        }

        .feature-icon {
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 20px;
        }

        .footer {
            background: var(--dark);
            color: white;
            padding: 50px 0 20px;
            margin-top: 80px;
        }

        .attraction-tag {
            background: #e3f2fd;
            color: #1976d2;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
            margin: 2px;
            display: inline-block;
        }

        .cuisine-tag {
            background: #fff3e0;
            color: #f57c00;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
            margin: 2px;
            display: inline-block;
        }

        .salary-badge {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-mountain-sun me-2"></i>
                Discover Georgia
            </a>
            <div class="navbar-nav me-auto">
                <a class="nav-link" href="/">Главная</a>
                <a class="nav-link" href="/cities">Города</a>
                <a class="nav-link" href="/about">О проекте</a>
            </div>
            <div class="navbar-nav">
                {% if current_user.is_authenticated %}
                    <a class="nav-link" href="/profile"><i class="fas fa-user me-1"></i> {{ current_user.username }}</a>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt me-1"></i> Выйти</a>
                {% else %}
                    <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt me-1"></i> Вход</a>
                    <a class="btn btn-primary ms-2" href="/register">Регистрация</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="hero-section">
        <div class="container text-center position-relative">
            <h1 class="display-3 fw-bold mb-4">Добро пожаловать в Грузию</h1>
            <p class="lead mb-5 fs-5">Откройте для себя страну древней культуры, гостеприимных людей и невероятной природы</p>
            <div class="d-flex flex-wrap justify-content-center gap-3">
                <a href="/cities" class="btn btn-light btn-lg px-4">
                    <i class="fas fa-map-marked-alt me-2"></i>Исследовать города
                </a>
                <a href="/register" class="btn btn-outline-light btn-lg px-4">
                    <i class="fas fa-user-plus me-2"></i>Присоединиться
                </a>
            </div>
        </div>
    </div>

    <div class="container mt-5 pt-5">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {{ content|safe }}
    </div>

    <footer class="footer">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5><i class="fas fa-mountain-sun me-2"></i>Discover Georgia</h5>
                    <p>Ваш надежный гид по удивительной стране Грузии. Откройте для себя древнюю культуру, вкуснейшую кухню и гостеприимство грузинского народа.</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <p>&copy; 2024 Discover Georgia. Все права защищены.</p>
                    <p>Сделано с ❤️ для любителей Грузии</p>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

# Главная страница
index_content = '''
<div class="row mb-5">
    <div class="col-12 text-center">
        <h2 class="section-title">Почему стоит посетить Грузию?</h2>
    </div>
</div>

<div class="row g-4 mb-5">
    <div class="col-md-3">
        <div class="stat-card">
            <div class="feature-icon">
                <i class="fas fa-wine-bottle"></i>
            </div>
            <h5>8000 лет виноделия</h5>
            <p class="text-muted">Грузия - родина виноделия с древнейшими традициями</p>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <div class="feature-icon">
                <i class="fas fa-utensils"></i>
            </div>
            <h5>Уникальная кухня</h5>
            <p class="text-muted">Хачапури, хинкали и другие кулинарные шедевры</p>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <div class="feature-icon">
                <i class="fas fa-mountain"></i>
            </div>
            <h5>Разнообразная природа</h5>
            <p class="text-muted">От альпийских лугов до черноморских пляжей</p>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <div class="feature-icon">
                <i class="fas fa-history"></i>
            </div>
            <h5>Богатая история</h5>
            <p class="text-muted">3000 лет государственности и культуры</p>
        </div>
    </div>
</div>

<div class="row mb-5">
    <div class="col-12 text-center">
        <h2 class="section-title">Популярные города</h2>
    </div>
</div>

<div class="row g-4">
    {% for city, info in cities.items() %}
    <div class="col-lg-6">
        <div class="card city-card">
            <div class="city-header" style="background: {{ info.color }};">
                <div class="city-icon">{{ info.icon }}</div>
                <div class="city-badge">{{ info.specialty }}</div>
            </div>
            <div class="card-body">
                <h4 class="card-title fw-bold">{{ city }}</h4>
                <p class="card-text">{{ info.description }}</p>

                <div class="row mb-3">
                    <div class="col-md-6">
                        <p><i class="fas fa-users me-2 text-primary"></i><strong>Население:</strong> {{ info.population }}</p>
                        <p><i class="fas fa-ruler-combined me-2 text-primary"></i><strong>Площадь:</strong> {{ info.area }}</p>
                        <p><i class="fas fa-temperature-low me-2 text-primary"></i><strong>Климат:</strong> {{ info.climate }}</p>
                    </div>
                    <div class="col-md-6">
                        <div class="salary-badge">
                            <i class="fas fa-wallet me-2"></i>{{ info.average_salary }}
                        </div>
                        <p class="mt-2"><i class="fas fa-calendar me-2 text-primary"></i><strong>Основан:</strong> {{ info.foundation }}</p>
                        <p><i class="fas fa-map-marker-alt me-2 text-primary"></i><strong>Координаты:</strong> {{ info.coordinates }}</p>
                    </div>
                </div>

                <div class="mb-3">
                    <strong><i class="fas fa-landmark me-2"></i>Достопримечательности:</strong><br>
                    {% for attraction in info.attractions %}
                    <span class="attraction-tag">{{ attraction }}</span>
                    {% endfor %}
                </div>

                <div class="mb-3">
                    <strong><i class="fas fa-utensils me-2"></i>Местная кухня:</strong><br>
                    {% for dish in info.cuisine %}
                    <span class="cuisine-tag">{{ dish }}</span>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

<div class="row mt-5">
    <div class="col-12 text-center">
        <div class="card bg-light border-0">
            <div class="card-body py-5">
                <h3 class="mb-3">Готовы к путешествию?</h3>
                <p class="text-muted mb-4">Присоединяйтесь к нашему сообществу путешественников</p>
                {% if not current_user.is_authenticated %}
                <a href="/register" class="btn btn-primary btn-lg">
                    <i class="fas fa-user-plus me-2"></i>Присоединиться
                </a>
                {% else %}
                <a href="/cities" class="btn btn-primary btn-lg">
                    <i class="fas fa-compass me-2"></i>Исследовать
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>
'''

# Страница регистрации
register_content = '''
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-primary text-white text-center">
                <h4 class="card-title mb-0"><i class="fas fa-user-plus me-2"></i>Регистрация</h4>
            </div>
            <div class="card-body p-4">
                <form method="POST" action="">
                    <div class="mb-3">
                        <label for="username" class="form-label">Имя пользователя</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="email" class="form-label">Email</label>
                        <input type="email" class="form-control" id="email" name="email" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Пароль</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 py-2">Создать аккаунт</button>
                </form>
                <div class="mt-3 text-center">
                    <p>Уже есть аккаунт? <a href="/login">Войдите здесь</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
'''

# Страница входа
login_content = '''
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-primary text-white text-center">
                <h4 class="card-title mb-0"><i class="fas fa-sign-in-alt me-2"></i>Вход в систему</h4>
            </div>
            <div class="card-body p-4">
                <form method="POST" action="">
                    <div class="mb-3">
                        <label for="username" class="form-label">Имя пользователя</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Пароль</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="remember" name="remember">
                        <label class="form-check-label" for="remember">Запомнить меня</label>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 py-2">Войти</button>
                </form>
                <div class="mt-3 text-center">
                    <p>Нет аккаунта? <a href="/register">Зарегистрируйтесь здесь</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
'''


# Страница профиля
def get_profile_content():
    content = f'''
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-primary text-white text-center">
                    <h4 class="card-title mb-0"><i class="fas fa-user-circle me-2"></i>Профиль пользователя</h4>
                </div>
                <div class="card-body p-4">
                    <div class="row">
                        <div class="col-md-8">
                            <p><i class="fas fa-user me-2 text-primary"></i><strong>Имя пользователя:</strong> {current_user.username}</p>
                            <p><i class="fas fa-envelope me-2 text-primary"></i><strong>Email:</strong> {current_user.email}</p>
                            <p><i class="fas fa-calendar me-2 text-primary"></i><strong>Дата регистрации:</strong> {current_user.date_created.strftime("%d.%m.%Y")}</p>
    '''

    if current_user.last_login:
        content += f'''
                            <p><i class="fas fa-clock me-2 text-primary"></i><strong>Последний вход:</strong> {current_user.last_login.strftime("%d.%m.%Y %H:%M")}</p>
        '''

    content += '''
                        </div>
                    </div>
                    <div class="mt-4">
                        <a href="/cities" class="btn btn-primary me-2"><i class="fas fa-map-marked-alt me-2"></i>Исследовать города</a>
                        <a href="/" class="btn btn-outline-primary"><i class="fas fa-home me-2"></i>На главную</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return content


# Страница "О проекте"
about_content = '''
<div class="row">
    <div class="col-md-8 mx-auto">
        <div class="card">
            <div class="card-body p-4">
                <h2 class="card-title text-center mb-4">О проекте Discover Georgia</h2>
                <p class="lead text-center mb-4">Ваш надежный гид по удивительной стране Грузии</p>

                <div class="row mb-4">
                    <div class="col-md-6">
                        <h4><i class="fas fa-target me-2 text-primary"></i>Наша миссия</h4>
                        <p>Помочь путешественникам открыть для себя настоящую Грузию - её культуру, кухню, историю и гостеприимство местных жителей.</p>
                    </div>
                    <div class="col-md-6">
                        <h4><i class="fas fa-eye me-2 text-primary"></i>Наше видение</h4>
                        <p>Стать самым полным и достоверным источником информации о Грузии для русскоязычных путешественников.</p>
                    </div>
                </div>

                <div class="text-center mt-4">
                    <a href="/" class="btn btn-primary me-2"><i class="fas fa-home me-2"></i>На главную</a>
                    <a href="/cities" class="btn btn-outline-primary"><i class="fas fa-city me-2"></i>Исследовать города</a>
                </div>
            </div>
        </div>
    </div>
</div>
'''


# Маршруты
@app.route("/")
def home():
    cities_data = get_cities_data()
    return render_template_string(base_html.replace('{{ content|safe }}', index_content), cities=cities_data)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Этот email уже используется', 'danger')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect('/login')

    return render_template_string(base_html.replace('{{ content|safe }}', register_content))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Вы успешно вошли! Добро пожаловать!', 'success')
            return redirect('/')
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template_string(base_html.replace('{{ content|safe }}', login_content))


@app.route("/logout")
def logout():
    logout_user()
    flash('Вы вышли из системы. Возвращайтесь скорее!', 'info')
    return redirect('/')


@app.route("/profile")
@login_required
def profile():
    profile_html_content = get_profile_content()
    return render_template_string(base_html.replace('{{ content|safe }}', profile_html_content))


@app.route("/cities")
def cities():
    cities_data = get_cities_data()
    return render_template_string(base_html.replace('{{ content|safe }}', index_content), cities=cities_data)


@app.route("/about")
def about():
    return render_template_string(base_html.replace('{{ content|safe }}', about_content))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🚀 Discover Georgia запущен!")
    print("📍 http://127.0.0.1:5000")
    print("🇬🇪 Добро пожаловать в Грузию!")
    app.run(debug=True, host='0.0.0.0', port=5000)