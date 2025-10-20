from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
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
    weather_data = None
    search_form = CitySearchForm()
    task_form = WeatherTaskForm()

    tasks = WeatherTask.objects.filter(user=request.user)
    search_history = CitySearchHistory.objects.filter(user=request.user)[:5]

    if request.method == 'POST' and 'search_city' in request.POST:
        search_form = CitySearchForm(request.POST)
        if search_form.is_valid():
            city_name = search_form.cleaned_data['city']
            weather_service = WeatherService()

            api_result = weather_service.get_weather(city_name)

            if 'error' in api_result:
                messages.error(request, f'❌ {api_result["error"]}')
            else:
                formatted_weather = weather_service.format_weather_display(api_result)
                if 'error' in formatted_weather:
                    messages.error(request, f'❌ {formatted_weather["error"]}')
                else:
                    weather_data = formatted_weather
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

    if request.method == 'POST' and 'create_task' in request.POST:
        task_form = WeatherTaskForm(request.POST)
        if task_form.is_valid():
            task = task_form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, '✅ Задача успешно создана!')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Исправьте ошибки в форме задачи.')

    context = {
        'weather_data': weather_data,
        'search_form': search_form,
        'task_form': task_form,
        'tasks': tasks,
        'search_history': search_history,
    }
    return render(request, 'dashboard/dashboard.html', context)


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