# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from urllib.parse import urlencode
from .forms import CustomUserCreationForm, WeatherSearchForm, TaskForm, WeatherRuleForm
from .models import SearchHistory, WeatherTask, WeatherRule
from .weather_service import get_weather_data
import json


def generate_automatic_tasks(user, city, weather_data):
    """Генерирует автоматические задачи на основе погодных условий"""
    created_tasks = []
    
    rain_prob = weather_data.get('rain_probability', 0)
    weather_main = weather_data.get('weather_main', '')
    temperature = weather_data.get('temperature', 0)
    humidity = weather_data.get('humidity', 0)

    if rain_prob >= 70:
        task_desc = "Взять зонт — возможен дождь"
        if not WeatherTask.objects.filter(
            user=user, city=city, description=task_desc, completed=False
        ).exists():
            task = WeatherTask.objects.create(
                user=user,
                city=city,
                description=task_desc,
                is_automatic=True,
                weather_condition='rain_high'
            )
            created_tasks.append(task)

    if temperature < -5:
        task_desc = "Надеть тёплую куртку и перчатки"
        if not WeatherTask.objects.filter(
            user=user, city=city, description=task_desc, completed=False
        ).exists():
            task = WeatherTask.objects.create(
                user=user,
                city=city,
                description=task_desc,
                is_automatic=True,
                weather_condition='cold_extreme'
            )
            created_tasks.append(task)

    if temperature > 30:
        task_desc = "Нанести солнцезащитный крем и взять воду"
        if not WeatherTask.objects.filter(
            user=user, city=city, description=task_desc, completed=False
        ).exists():
            task = WeatherTask.objects.create(
                user=user,
                city=city,
                description=task_desc,
                is_automatic=True,
                weather_condition='hot_extreme'
            )
            created_tasks.append(task)

    if humidity > 90 and temperature > 25:
        task_desc = "Возможна духота — проветрить помещение"
        if not WeatherTask.objects.filter(
            user=user, city=city, description=task_desc, completed=False
        ).exists():
            task = WeatherTask.objects.create(
                user=user,
                city=city,
                description=task_desc,
                is_automatic=True,
                weather_condition='humidity_high'
            )
            created_tasks.append(task)

    user_rules = WeatherRule.objects.filter(user=user, is_active=True)
    for rule in user_rules:
        if rule.check_condition(weather_data):
            if not WeatherTask.objects.filter(
                user=user, city=city, description=rule.task_description, completed=False
            ).exists():
                task = WeatherTask.objects.create(
                    user=user,
                    city=city,
                    description=rule.task_description,
                    is_automatic=True,
                    weather_condition=f'user_rule_{rule.id}'
                )
                created_tasks.append(task)
    
    return created_tasks

def get_city_icon(city_name):
    """
    Возвращает иконку Font Awesome для города.
    """
    city_icons = {
        # Столицы
        'Moscow': 'fas fa-landmark',
        'London': 'fas fa-crown',
        'Paris': 'fas fa-monument',
        'Berlin': 'fas fa-landmark',
        'Rome': 'fas fa-monument',
        'Madrid': 'fas fa-landmark',
        'Washington': 'fas fa-landmark',
        'Tokyo': 'fas fa-landmark',
        'Beijing': 'fas fa-landmark',
        'New Delhi': 'fas fa-landmark',

        'New York': 'fas fa-city',
        'Los Angeles': 'fas fa-city',
        'Chicago': 'fas fa-city',
        'Houston': 'fas fa-city',
        'Phoenix': 'fas fa-city',
        'Philadelphia': 'fas fa-city',
        'San Antonio': 'fas fa-city',
        'San Diego': 'fas fa-city',
        'Dallas': 'fas fa-city',
        'San Jose': 'fas fa-city',

        'Sochi': 'fas fa-umbrella-beach',
        'Nice': 'fas fa-umbrella-beach',
        'Barcelona': 'fas fa-umbrella-beach',
        'Miami': 'fas fa-umbrella-beach',
        'Venice': 'fas fa-water',
        'Amsterdam': 'fas fa-water',
        'Hamburg': 'fas fa-water',

        'Las Vegas': 'fas fa-dice',
        'Orlando': 'fas fa-magic',
        'Disneyland': 'fas fa-magic',
    }
    
    city_lower = city_name.lower()
    for city, icon in city_icons.items():
        if city.lower() == city_lower:
            return icon

    if any(word in city_lower for word in ['beach', 'coast', 'sea', 'ocean', 'port']):
        return 'fas fa-umbrella-beach'
    elif any(word in city_lower for word in ['mountain', 'alps', 'peak', 'hill']):
        return 'fas fa-mountain'
    elif any(word in city_lower for word in ['forest', 'wood', 'park']):
        return 'fas fa-tree'
    elif any(word in city_lower for word in ['desert', 'sahara']):
        return 'fas fa-sun'
    else:
        return 'fas fa-city'

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать в ваш персональный погодный дашборд.')
            return render(request, 'dashboard/registration_success.html')
    else:
        form = CustomUserCreationForm()
    return render(request, 'dashboard/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'dashboard/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def handle_search_city(request):
    """Обработчик для поиска погоды по городу."""
    form = WeatherSearchForm(request.POST)
    if form.is_valid():
        current_city = form.cleaned_data['city']
        request.session['current_city'] = current_city

        # Получаем данные о погоде и обрабатываем ошибки
        weather = get_weather_for_city(current_city)
        if weather:
            save_search_history(request.user, weather['city'])
            generate_tasks_from_weather(request.user, weather)
        return weather
    else:
        # Если форма не валидна, возвращаем сообщение об ошибке
        return None, "Некорректное название города"


def get_weather_for_city(city):
    """Получение данных о погоде, обработка ошибок."""
    try:
        return get_weather_data(city)
    except Exception as e:
        # Обработка исключений, если что-то пошло не так
        return None


def save_search_history(user, city):
    """Сохранение истории поиска."""
    SearchHistory.objects.create(user=user, city=city)


def generate_tasks_from_weather(user, weather):
    """Генерация автоматических задач на основе данных о погоде."""
    new_automatic_tasks = generate_automatic_tasks(user, weather['city'], weather)
    if new_automatic_tasks:
        messages.info(user.request, f'Создано {len(new_automatic_tasks)} автоматических задач на основе погоды!')


def main_handler(request):
    """Основной обработчик запроса."""
    if request.method == 'POST':
        if 'search_city' in request.POST:
            weather, error = handle_search_city(request)
            if error:
                current_city = request.session.get('current_city', 'Санкт-Петербург')
                weather = get_weather_for_city(current_city)
        elif 'add_task' in request.POST:
            task_form = TaskForm(request.POST)
            # Дополнительная логика по добавлению задачи (не предоставлена в исходном коде)
                        
                # === ПРОВЕРКА СУЩЕСТВОВАНИЯ ГОРОДА ===
                def handle_city_and_weather(request):
    # Получение текущего города из сессии, если он не указан
    current_city = request.session.get('current_city', 'Санкт-Петербург')

    # Проверка POST-запроса
    if request.method == 'POST':
        city_from_form = request.POST.get('city')
        if not city_from_form:
            messages.error(request, 'Не указан город для задачи')
        else:
            try:
                # Получаем данные о погоде для указанного города
                weather_check = get_weather_data(city_from_form)
                city = weather_check['city']

                # Создание новой задачи
                WeatherTask.objects.create(
                    user=request.user,
                    city=city,
                    description=request.POST.get('description')
                )
                messages.success(request, 'Задача добавлена!')
                current_city = city
                request.session['current_city'] = current_city

                # Генерация автоматических задач
                create_automatic_tasks(request.user, current_city)

            except Exception:
                messages.error(request, f'Невозможно добавить задачу: город "{city_from_form}" не найден')

    else:  # Обработка GET-запроса
        current_city = request.POST.get('city', current_city)
        request.session['current_city'] = current_city

    # Получение данных о погоде для текущего города
    weather = fetch_weather_data(current_city)

    # Перенаправление
    return HttpResponseRedirect(f"{request.path}?{urlencode({'filter': task_filter})}")


def fetch_weather_data(city):
    """ Получение данных о погоде и форматирование времени. """
    try:
        weather = get_weather_data(city)
        if 'formatted_time' not in weather and 'timestamp' in weather:
            from datetime import datetime
            timestamp_str = weather['timestamp'].replace('Z', '+00:00')
            timestamp_dt = datetime.fromisoformat(timestamp_str)
            weather['formatted_time'] = timestamp_dt.strftime('%d.%m.%Y %H:%M')
        return weather
    except Exception:
        return None


def create_automatic_tasks(user, current_city):
    """ Генерация автоматических задач на основе погоды. """
    weather = fetch_weather_data(current_city)
    if weather:
        new_automatic_tasks = generate_automatic_tasks(user, current_city, weather)
        if new_automatic_tasks:
            messages.info(request, f'Создано {len(new_automatic_tasks)} автоматических задач на основе погоды!')
            return HttpResponseRedirect(f"{request.path}?{urlencode({'filter': task_filter})}")
    # GET-запрос
    else:
        current_city = request.session.get('current_city', 'Санкт-Петербург')
        try:
            weather = get_weather_data(current_city)
            # Генерируем автоматические задачи
            new_automatic_tasks = generate_automatic_tasks(request.user, current_city, weather)
            if new_automatic_tasks:
                messages.info(request, f'Создано {len(new_automatic_tasks)} автоматических задач на основе погоды!')
        except Exception as e:
            weather = None
    
    tasks_queryset = WeatherTask.objects.filter(user=request.user, city=current_city)
    if task_filter == 'active':
        tasks_queryset = tasks_queryset.filter(completed=False)
    elif task_filter == 'completed':
        tasks_queryset = tasks_queryset.filter(completed=True)
    
    tasks = tasks_queryset
    history = SearchHistory.objects.filter(user=request.user)[:10]
    city_icon = get_city_icon(current_city) if current_city else 'fas fa-city'
    
    search_form = WeatherSearchForm(initial={'city': current_city})
    task_form = TaskForm()
    
    context = {
        'search_form': search_form,
        'task_form': task_form,
        'weather': weather,
        'error': error,
        'tasks': tasks,
        'history': history,
        'current_city': current_city,
        'task_filter': task_filter,
        'city_icon': city_icon,
    }
    return render(request, 'dashboard/index.html', context)
    pass

def index(request):
    """
    Главная страница для всех пользователей.
    Если авторизован - показывает дашборд, иначе - форму входа/регистрации.
    """
    if request.user.is_authenticated:
        # Для авторизованных перенаправляем на дашборд
        return dashboard(request)
    else:
        # Для неавторизованных показываем приветственную страницу
        return render(request, 'dashboard/index.html', {
            'not_authenticated': True
        })

@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import WeatherTask


@login_required
def toggle_task_ajax(request, task_id):
    """AJAX-обработчик для переключения статуса задачи"""
    if request.method == 'POST':
        return toggle_task_status(request, task_id)

    return invalid_request_response()


def toggle_task_status(request, task_id):
    """Переключает статус задачи и возвращает JSON-ответ"""
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    return success_response(task)


def success_response(task):
    """Создает успешный JSON-ответ при переключении статуса задачи"""
    return JsonResponse({
        'success': True,
        'completed': task.completed,
        'message': f'Задача "{task.description}" {"выполнена" if task.completed else "отменена"}!'
    })


def invalid_request_response():
    """Создает ответ на недопустимый метод запроса"""
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    task.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def clear_history(request):
    if request.method == 'POST':
        SearchHistory.objects.filter(user=request.user).delete()
        messages.success(request, 'История поиска очищена!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import WeatherRuleForm
from .models import WeatherRule


@login_required
def weather_rules(request):
    """Страница управления правилами погоды"""
    if request.method == 'POST':
        return handle_post_request(request)

    form = WeatherRuleForm()
    rules = get_user_weather_rules(request.user)
    return render_weather_rules_page(request, form, rules)


@login_required
def handle_post_request(request):
    form = WeatherRuleForm(request.POST)
    if form.is_valid():
        save_weather_rule(form, request.user)
        messages.success(request, 'Правило успешно создано!')
        return redirect('weather_rules')

    return render(request, 'dashboard/weather_rules.html', {
        'form': form,
        'rules': get_user_weather_rules(request.user)
    })


def save_weather_rule(form, user):
    """Сохраняет правило погоды и ассоциирует его с пользователем"""
    rule = form.save(commit=False)
    rule.user = user
    rule.save()


def get_user_weather_rules(user):
    """Получает все правила погоды пользователя"""
    return WeatherRule.objects.filter(user=user).order_by('-created_at')


def render_weather_rules_page(request, form, rules):
    """Отображает страницу с правилами погоды"""
    return render(request, 'dashboard/weather_rules.html', {
        'form': form,
        'rules': rules
    })

@login_required
def toggle_rule(request, rule_id):
    """Включение/выключение правила"""
    rule = get_object_or_404(WeatherRule, id=rule_id, user=request.user)
    rule.is_active = not rule.is_active
    rule.save()
    status = "включено" if rule.is_active else "выключено"
    messages.success(request, f'Правило "{rule.name}" {status}!')
    return redirect('weather_rules')

@login_required
def delete_rule(request, rule_id):
    """Удаление правила"""
    rule = get_object_or_404(WeatherRule, id=rule_id, user=request.user)
    rule_name = rule.name
    rule.delete()
    messages.success(request, f'Правило "{rule_name}" удалено!')
    return redirect('weather_rules')
