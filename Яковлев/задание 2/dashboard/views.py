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


def create_weather_task(user, city, task_desc, weather_condition):
    if not WeatherTask.objects.filter(
        user=user, city=city, description=task_desc, completed=False
    ).exists():
        return WeatherTask.objects.create(
            user=user,
            city=city,
            description=task_desc,
            is_automatic=True,
            weather_condition=weather_condition
        )
    return None

def generate_automatic_tasks(user, city, weather_data):
    created_tasks = []
    
    rain_prob = weather_data.get('rain_probability', 0)
    temperature = weather_data.get('temperature', 0)
    humidity = weather_data.get('humidity', 0)
    
    tasks_conditions = [
        (rain_prob >= 70, "Взять зонт — возможен дождь", 'rain_high'),
        (temperature < -5, "Надеть тёплую куртку и перчатки", 'cold_extreme'),
        (temperature > 30, "Нанести солнцезащитный крем и взять воду", 'hot_extreme'),
        (humidity > 90 and temperature > 25, "Возможна духота — проветрить помещение", 'humidity_high'),
    ]
    
    for condition, description, weather_condition in tasks_conditions:
        if condition:
            task = create_weather_task(user, city, description, weather_condition)
            if task:
                created_tasks.append(task)
    
    user_rules = WeatherRule.objects.filter(user=user, is_active=True)
    for rule in user_rules:
        if rule.check_condition(weather_data):
            task = create_weather_task(user, city, rule.task_description, f'user_rule_{rule.id}')
            if task:
                created_tasks.append(task)
    
    return created_tasks

def get_city_by_icon(icon_class):
    city_icons = {
        'fas fa-landmark': [
            'Moscow', 'Berlin', 'Madrid', 'Washington', 'Tokyo', 'Beijing', 'New Delhi',
            'Sochi', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 
            'San Antonio', 'San Diego', 'Dallas', 'San Jose',
        ],
        'fas fa-crown': ['London'],
        'fas fa-monument': ['Paris', 'Rome', 'Barcelona'],
        'fas fa-umbrella-beach': ['Nice', 'Miami'],
        'fas fa-water': ['Venice', 'Amsterdam', 'Hamburg'],
        'fas fa-dice': ['Las Vegas'],
        'fas fa-magic': ['Orlando', 'Disneyland'],
    }

    cities = city_icons.get(icon_class)
    return cities if cities else None
   
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
    task_filter = request.GET.get('filter', 'all')
    current_city = request.session.get('current_city', 'Санкт-Петербург')
    weather = None
    error = request.session.get('weather_error')  # Получаем ошибку из сессии

    if error:
        request.session.pop('weather_error', None)

    if request.method == 'POST':
        if 'search_city' in request.POST:
            return _handle_city_search(request, task_filter)
        elif 'add_task' in request.POST:
            return _handle_task_creation(request, task_filter)


    if not error: 
        try:
            weather = get_weather_data(current_city)
            _generate_and_notify_automatic_tasks(request, current_city, weather)
        except Exception as e:
            weather = None

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



def _handle_city_search(request, task_filter):
    form = WeatherSearchForm(request.POST)
    current_city = 'Санкт-Петербург'
    error = None

    if form.is_valid():
        current_city = form.cleaned_data['city']
        try:
            weather = get_weather_data(current_city)
            _update_search_history(request.user, weather['city'])
            current_city = weather['city']
            request.session['current_city'] = current_city
            _generate_and_notify_automatic_tasks(request, current_city, weather)
        except Exception as e:
            error = str(e)
    else:
        error = "Некорректное название города"
        # Можно также получить конкретные ошибки из формы:
        # error = form.errors.get('city', ['Некорректное название города'])[0]

    final_city = current_city if not error else request.session.get('current_city', 'Санкт-Петербург')
    request.session['current_city'] = final_city

    if error:
        request.session['weather_error'] = error
    else:
        request.session.pop('weather_error', None)

    return _redirect_with_weather(request, final_city, task_filter)


def _update_search_history(user, city):
 
    from django.utils import timezone
    SearchHistory.objects.filter(user=user, city=city).delete()
    SearchHistory.objects.create(user=user, city=city, timestamp=timezone.now())

def _handle_task_creation(request, task_filter):
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
    new_tasks = generate_automatic_tasks(request.user, city, weather_data)
    if new_tasks:
        messages.info(request, f'Создано {len(new_tasks)} автоматических задач на основе погоды!')


def _get_filtered_tasks(user, city, task_filter):
    tasks_queryset = WeatherTask.objects.filter(user=user, city=city)
    if task_filter == 'active':
        return tasks_queryset.filter(completed=False)
    elif task_filter == 'completed':
        return tasks_queryset.filter(completed=True)
    return tasks_queryset

def index(request):
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
    rule = get_object_or_404(WeatherRule, id=rule_id, user=request.user)
    rule.is_active = not rule.is_active
    rule.save()
    status = "включено" if rule.is_active else "выключено"
    messages.success(request, f'Правило "{rule.name}" {status}!')
    return redirect('weather_rules')

@login_required
def delete_rule(request, rule_id):
    rule = get_object_or_404(WeatherRule, id=rule_id, user=request.user)
    rule_name = rule.name
    rule.delete()
    messages.success(request, f'Правило "{rule_name}" удалено!')
    return redirect('weather_rules')






