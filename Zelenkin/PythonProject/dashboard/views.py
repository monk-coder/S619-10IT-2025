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
        return render(request, 'dashboard/login.html', {'user': request.user})

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
    """Основной view дашборда с улучшенной структурой"""
    # Обрабатываем POST запросы
    if request.method == 'POST':
        response = handle_post_request(request)
        if response:
            return response

    # Рендерим страницу с контекстом
    return render_dashboard(request)


def handle_post_request(request):
    """Обработка всех POST запросов дашборда"""
    if 'search_city' in request.POST:
        handle_city_search(request)
    elif 'create_task' in request.POST:
        return handle_task_creation(request)
    return None


def handle_city_search(request):
    """Обработка поиска города"""
    form = CitySearchForm(request.POST)
    if not form.is_valid():
        return

    city_name = form.cleaned_data['city']
    weather_service = WeatherService()

    # Получаем и валидируем данные погоды
    weather_data = get_validated_weather_data(weather_service, city_name, request)
    if not weather_data:
        return

    # Сохраняем историю и показываем результат
    save_search_history(request.user, weather_data)
    show_weather_success(request, weather_data)

    # Сохраняем данные погоды в сессии
    request.session['last_weather_data'] = weather_data


def get_validated_weather_data(weather_service, city_name, request):
    """Получение и валидация данных погоды"""
    api_result = weather_service.get_weather(city_name)
    if 'error' in api_result:
        messages.error(request, f'❌ {api_result["error"]}')
        return None

    formatted_weather = weather_service.format_weather_display(api_result)
    if 'error' in formatted_weather:
        messages.error(request, f'❌ {formatted_weather["error"]}')
        return None

    return formatted_weather


def save_search_history(user, weather_data):
    """Сохранение истории поиска"""
    CitySearchHistory.objects.create(
        user=user,
        city_name=weather_data['city'],
        country=weather_data['country']
    )


def show_weather_success(request, weather_data):
    """Показать сообщение об успешном получении погоды"""
    messages.success(
        request,
        f'✅ Погода для {weather_data["city"]} загружена! '
        f'Температура: {weather_data["temperature"]}°C'
    )


def handle_task_creation(request):
    """Обработка создания задачи"""
    form = WeatherTaskForm(request.POST)
    if not form.is_valid():
        messages.error(request, '❌ Исправьте ошибки в форме задачи.')
        return None

    task = form.save(commit=False)
    task.user = request.user
    task.save()
    messages.success(request, '✅ Задача успешно создана!')
    return redirect('dashboard')


def render_dashboard(request):
    """Рендеринг страницы дашборда с контекстом"""
    context = {
        'weather_data': request.session.get('last_weather_data'),
        'search_form': CitySearchForm(),
        'task_form': WeatherTaskForm(),
        'tasks': WeatherTask.objects.filter(user=request.user),
        'search_history': CitySearchHistory.objects.filter(user=request.user)[:5],
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def delete_task(request, task_id):
    """Удаление задачи"""
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, '🗑️ Задача удалена!')
    return redirect('dashboard')


@login_required
def toggle_task(request, task_id):
    """Переключение статуса задачи"""
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()

    status = "выполнена" if task.is_completed else "активна"
    messages.success(request, f'✅ Задача "{task.title}" отмечена как {status}')
    return redirect('dashboard')


@login_required
def clear_history(request):
    """Очистка истории поиска"""
    if request.method == 'POST':
        CitySearchHistory.objects.filter(user=request.user).delete()
        messages.success(request, '🧹 История поиска очищена!')
    return redirect('dashboard')