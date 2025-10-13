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
def dashboard(request):
    weather = None
    error = None
    task_filter = request.GET.get('filter', 'all')
    current_city = 'Санкт-Петербург'
    
    if request.method == 'POST':
        if 'search_city' in request.POST:
            form = WeatherSearchForm(request.POST)
            if form.is_valid():
                current_city = form.cleaned_data['city']
                request.session['current_city'] = current_city
                
                try:
                    weather = get_weather_data(current_city)
                    SearchHistory.objects.create(user=request.user, city=weather['city'])
                    current_city = weather['city']
                    request.session['current_city'] = current_city
                    # Генерируем автоматические задачи
                    new_automatic_tasks = generate_automatic_tasks(request.user, current_city, weather)
                    if new_automatic_tasks:
                        messages.info(request, f'Создано {len(new_automatic_tasks)} автоматических задач на основе погоды!')
                except Exception as e:
                    error = str(e)
                    weather = None
            else:
                error = "Некорректное название города"
                current_city = request.session.get('current_city', 'Санкт-Петербург')
                try:
                    weather = get_weather_data(current_city)
                except Exception as e:
                    weather = None
        
        elif 'add_task' in request.POST:
            task_form = TaskForm(request.POST)
            if task_form.is_valid():
                description = task_form.cleaned_data['description']
                # Берём город именно из формы задачи (скрытое поле)
                city_from_form = request.POST.get('city', '').strip()
                        
                # === ПРОВЕРКА СУЩЕСТВОВАНИЯ ГОРОДА ===
                if not city_from_form:
                    messages.error(request, 'Не указан город для задачи')
                    current_city = request.session.get('current_city', 'Санкт-Петербург')
                else:
                    try:
                        # Проверяем именно этот город
                        weather_check = get_weather_data(city_from_form)
                        city = weather_check['city']  # Используем корректное название от API
                
                        WeatherTask.objects.create(
                            user=request.user,
                            city=city,
                            description=description
                        )
                        messages.success(request, 'Задача добавлена!')
                        current_city = city
                        request.session['current_city'] = current_city
                        # Генерируем автоматические задачи
                        new_automatic_tasks = generate_automatic_tasks(request.user, current_city, weather)
                        if new_automatic_tasks:
                            messages.info(request, f'Создано {len(new_automatic_tasks)} автоматических задач на основе погоды!')
                    except Exception as e:
                        messages.error(request, f'Невозможно добавить задачу: город "{city_from_form}" не найден')
                        # Оставляем текущий город без изменений
                        current_city = request.session.get('current_city', 'Санкт-Петербург')
            else:
                current_city = request.POST.get('city', request.session.get('current_city', 'Санкт-Петербург'))
                request.session['current_city'] = current_city
    
            # Получаем погоду для текущего города (того, что в сессии)
            try:
                weather = get_weather_data(current_city)
                if 'formatted_time' not in weather and 'timestamp' in weather:
                    from datetime import datetime
                    try:
                        timestamp_str = weather['timestamp'].replace('Z', '+00:00')
                        timestamp_dt = datetime.fromisoformat(timestamp_str)
                        weather['formatted_time'] = timestamp_dt.strftime('%d.%m.%Y %H:%M')
                    except:
                        weather['formatted_time'] = 'Неизвестно'
            except Exception as e:
                weather = None
    
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