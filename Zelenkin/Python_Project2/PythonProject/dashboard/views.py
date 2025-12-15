from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import CustomUserCreationForm, WeatherTaskForm, CitySearchForm
from .models import WeatherTask, CitySearchHistory
from .utils import WeatherService


def index(request):
    return render(request, 'dashboard/index.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'🎉 Добро пожаловать, {user.username}! Регистрация прошла успешно!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'dashboard/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'🌞 Добрый день, {username}! Рады видеть вас снова!')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Неверное имя пользователя или пароль')

    return render(request, 'dashboard/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'👋 До свидания, {username}! Прекрасного вам дня! 🌈')
    return redirect('index')


@login_required
def dashboard_view(request):
    weather_data = None

    # Обработка POST запросов
    if request.method == 'POST':
        if 'search_city' in request.POST:
            weather_data = handle_city_search(request)
        elif 'create_task' in request.POST:
            return handle_task_creation(request)

    # Получаем weather_data из сессии если нет нового поиска
    if not weather_data:
        weather_data = request.session.get('last_weather_data')

    # Подготовка контекста
    context = {
        'weather_data': weather_data,
        'search_form': CitySearchForm(),
        'task_form': WeatherTaskForm(),
        'tasks': WeatherTask.objects.filter(user=request.user),
        'search_history': CitySearchHistory.objects.filter(user=request.user)[:5],
    }
    return render(request, 'dashboard/dashboard.html', context)


def handle_city_search(request):
    """Обработка поиска города"""
    form = CitySearchForm(request.POST)
    if not form.is_valid():
        messages.error(request, '❌ Введите корректное название города')
        return None

    city_name = form.cleaned_data['city']
    weather_service = WeatherService()

    # Получаем данные погоды
    api_result = weather_service.get_weather(city_name)
    if 'error' in api_result:
        messages.error(request, f'❌ {api_result["error"]}')
        return None

    formatted_weather = weather_service.format_weather_display(api_result)
    if 'error' in formatted_weather:
        messages.error(request, f'❌ {formatted_weather["error"]}')
        return None

    # Сохраняем историю
    CitySearchHistory.objects.create(
        user=request.user,
        city_name=formatted_weather['city'],
        country=formatted_weather['country']
    )

    messages.success(
        request,
        f'✅ Погода для {formatted_weather["city"]} загружена! '
        f'Температура: {formatted_weather["temperature"]}°C'
    )

    # Сохраняем в сессии
    request.session['last_weather_data'] = formatted_weather
    return formatted_weather


def handle_task_creation(request):
    """Обработка создания задачи"""
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    related_city = request.POST.get('related_city', '').strip()

    if not title:
        messages.error(request, '❌ Название задачи не может быть пустым')
        return redirect('dashboard')

    # Создаем задачу
    task = WeatherTask(
        user=request.user,
        title=title,
        description=description,
        related_city=related_city
    )
    task.save()

    messages.success(request, '✅ Задача успешно создана!')
    return redirect('dashboard')


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, '🗑️ Задача удалена!')
    return redirect('dashboard')


@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()

    status = "выполнена" if task.is_completed else "активна"
    messages.success(request, f'✅ Задача "{task.title}" отмечена как {status}')
    return redirect('dashboard')


@login_required
def clear_history(request):
    if request.method == 'POST':
        CitySearchHistory.objects.filter(user=request.user).delete()
        messages.success(request, '🧹 История поиска очищена!')
    return redirect('dashboard')