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

    # Пользовательские правила
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
        
        # Крупные города
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
        
        # Курорты и приморские города
        'Sochi': 'fas fa-umbrella-beach',
        'Nice': 'fas fa-umbrella-beach',
        'Barcelona': 'fas fa-umbrella-beach',
        'Miami': 'fas fa-umbrella-beach',
        'Venice': 'fas fa-water',
        'Amsterdam': 'fas fa-water',
        'Hamburg': 'fas fa-water',
        
        # Города с известными достопримечательностями
        'Las Vegas': 'fas fa-dice',
        'Orlando': 'fas fa-magic',
        'Disneyland': 'fas fa-magic',
    }
    
    city_lower = city_name.lower()
    for city, icon in city_icons.items():
        if city.lower() == city_lower:
            return icon
    
    # Fallback иконки по ключевым словам
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
def dashboard(request):
    """Главная страница дашборда с обработкой всех действий пользователя"""
    task_filter = request.GET.get('filter', 'all')
    current_city = request.session.get('current_city', 'Санкт-Петербург')
    weather = None
    error = request.session.get('weather_error')  # Получаем ошибку из сессии

    # Очищаем ошибку из сессии после получения
    if error:
        request.session.pop('weather_error', None)

    # Обработка POST-запросов
    if request.method == 'POST':
        if 'search_city' in request.POST:
            return _handle_city_search(request, task_filter)
        elif 'add_task' in request.POST:
            return _handle_task_creation(request, task_filter)

    # Обработка GET-запроса (или после обработки POST без редиректа)
    if not error:  # Только если нет ошибки валидации
        try:
            weather = get_weather_data(current_city)
            _generate_and_notify_automatic_tasks(request, current_city, weather)
        except Exception as e:
            weather = None

    # Подготовка данных для шаблона
    tasks = _get_filtered_tasks(request.user, current_city, task_filter)
    history = SearchHistory.objects.filter(user=request.user)[:10]
    city_icon = get_city_icon(current_city) if current_city else 'fas fa-city'

    context = {
        'search_form': WeatherSearchForm(initial={'city': current_city}),
        'task_form': TaskForm(),
        'weather': weather,
        'error': error,
        'tasks': tasks,
        'history': history,
        'current_city': current_city,
        'task_filter': task_filter,
        'city_icon': city_icon,
    }
    return render(request, 'dashboard/index.html', context)


# === Вспомогательные функции ===

def _handle_city_search(request, task_filter):
    """Обработка поиска города"""
    form = WeatherSearchForm(request.POST)
    current_city = 'Санкт-Петербург'
    error = None

    if form.is_valid():
        current_city = form.cleaned_data['city']
        try:
            weather = get_weather_data(current_city)
            # === ОБНОВЛЕНИЕ ИСТОРИИ БЕЗ ДУБЛИКАТОВ ===
            _update_search_history(request.user, weather['city'])
            current_city = weather['city']
            request.session['current_city'] = current_city
            _generate_and_notify_automatic_tasks(request, current_city, weather)
        except Exception as e:
            error = str(e)
    else:
        # Валидация формы не прошла - получаем ошибки из формы
        error = "Некорректное название города"
        # Можно также получить конкретные ошибки из формы:
        # error = form.errors.get('city', ['Некорректное название города'])[0]

    # В любом случае получаем погоду для текущего города
    final_city = current_city if not error else request.session.get('current_city', 'Санкт-Петербург')
    request.session['current_city'] = final_city

    # Сохраняем ошибку в сессии для отображения в шаблоне
    if error:
        request.session['weather_error'] = error
    else:
        request.session.pop('weather_error', None)

    return _redirect_with_weather(request, final_city, task_filter)


def _update_search_history(user, city):
    """
    Удаляет старую запись о городе и создаёт новую (для корректной сортировки).
    """
    from django.utils import timezone
    SearchHistory.objects.filter(user=user, city=city).delete()
    SearchHistory.objects.create(user=user, city=city, timestamp=timezone.now())

def _handle_task_creation(request, task_filter):
    """Обработка создания задачи"""
    task_form = TaskForm(request.POST)
    city_from_form = request.POST.get('city', '').strip()
    current_city = request.session.get('current_city', 'Санкт-Петербург')

    if task_form.is_valid() and city_from_form:
        try:
            weather_check = get_weather_data(city_from_form)
            city = weather_check['city']

            WeatherTask.objects.create(
                user=request.user,
                city=city,
                description=task_form.cleaned_data['description']
            )
            messages.success(request, 'Задача добавлена!')
            current_city = city
            request.session['current_city'] = current_city
        except Exception as e:
            messages.error(request, f'Невозможно добавить задачу: город "{city_from_form}" не найден')
    else:
        if not city_from_form:
            messages.error(request, 'Не указан город для задачи')

    return _redirect_with_weather(request, current_city, task_filter)


def _redirect_with_weather(request, city, task_filter, error=None):
    """Получает погоду и возвращает редирект"""
    try:
        weather = get_weather_data(city)
        if 'formatted_time' not in weather and 'timestamp' in weather:
            from datetime import datetime
            try:
                timestamp_str = weather['timestamp'].replace('Z', '+00:00')
                timestamp_dt = datetime.fromisoformat(timestamp_str)
                weather['formatted_time'] = timestamp_dt.strftime('%d.%m.%Y %H:%M')
            except:
                weather['formatted_time'] = 'Неизвестно'
    except Exception:
        pass

    return HttpResponseRedirect(f"{request.path}?{urlencode({'filter': task_filter})}")


def _generate_and_notify_automatic_tasks(request, city, weather_data):
    """Генерирует автоматические задачи и показывает уведомление"""
    new_tasks = generate_automatic_tasks(request.user, city, weather_data)
    if new_tasks:
        messages.info(request, f'Создано {len(new_tasks)} автоматических задач на основе погоды!')


def _get_filtered_tasks(user, city, task_filter):
    """Возвращает отфильтрованные задачи"""
    tasks_queryset = WeatherTask.objects.filter(user=user, city=city)
    if task_filter == 'active':
        return tasks_queryset.filter(completed=False)
    elif task_filter == 'completed':
        return tasks_queryset.filter(completed=True)
    return tasks_queryset

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
def toggle_task_ajax(request, task_id):
    """AJAX-обработчик для переключения статуса задачи"""
    if request.method == 'POST':
        try:
            task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
            task.completed = not task.completed
            task.save()
            return JsonResponse({
                'success': True,
                'completed': task.completed,
                'message': f'Задача "{task.description}" {"выполнена" if task.completed else "отменена"}!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Ошибка при обновлении задачи'
            })
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

@login_required
def weather_rules(request):
    """Страница управления правилами погоды"""
    if request.method == 'POST':
        form = WeatherRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.user = request.user
            rule.save()
            messages.success(request, 'Правило успешно создано!')
            return redirect('weather_rules')
    else:
        form = WeatherRuleForm()
    
    rules = WeatherRule.objects.filter(user=request.user).order_by('-created_at')
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

