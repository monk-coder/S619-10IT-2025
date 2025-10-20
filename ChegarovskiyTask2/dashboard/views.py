from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .models import CitySearchHistory, WeatherTask, FavoriteCity, UserProfile, WeatherCache
from .weather_api import get_weather_data, get_cached_weather_data
from .forms import WeatherTaskForm, LanguageForm


def home(request):
    weather_data = None
    error_message = None
    city_tasks = []
    search_history = []
    favorite_cities = []

    if request.method == 'POST' and 'city' in request.POST:
        city_name = request.POST['city'].strip()
        if city_name:
            weather_data = get_cached_weather_data(city_name)

            if not weather_data:
                weather_data = get_weather_data(city_name)

            if weather_data:
                if request.user.is_authenticated:
                    CitySearchHistory.objects.create(user=request.user, city_name=city_name)
                    city_tasks = WeatherTask.objects.filter(
                        user=request.user, city_name__iexact=city_name
                    ).order_by('-created_at')
            else:
                error_message = "Не удалось найти погоду для этого города. Проверьте название."
        else:
            error_message = "Введите название города."

    # История поиска показывается всегда для авторизованных пользователей
    if request.user.is_authenticated:
        search_history = CitySearchHistory.objects.filter(
            user=request.user
        ).order_by('-searched_at')[:5]
        favorite_cities = list(FavoriteCity.objects.filter(
            user=request.user
        ).values_list('city_name', flat=True))

    return render(request, 'dashboard/home.html', {
        'weather_data': weather_data,
        'error_message': error_message,
        'city_tasks': city_tasks,
        'search_history': search_history,
        'favorite_cities': favorite_cities
    })


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            return redirect('home')
        else:
            messages.error(request, "Ошибка регистрации. Проверьте данные.")
    else:
        form = UserCreationForm()
    return render(request, 'dashboard/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Добро пожаловать, {username}!")
                return redirect('home')
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    else:
        form = AuthenticationForm()
    return render(request, 'dashboard/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect('home')


@login_required
def dashboard_view(request):
    tasks = WeatherTask.objects.filter(user=request.user).order_by('-created_at')
    search_history = CitySearchHistory.objects.filter(
        user=request.user
    ).order_by('-searched_at')[:5]

    if request.method == 'POST':
        city_name = request.POST.get('city_name', '').strip()
        task_text = request.POST.get('task_text', '').strip()
        if city_name and task_text:
            WeatherTask.objects.create(
                user=request.user,
                city_name=city_name,
                task_text=task_text
            )
            messages.success(request, "Задача добавлена!")
            return redirect('dashboard')
        else:
            messages.error(request, "Заполните все поля.")

    return render(request, 'dashboard/dashboard.html', {
        'tasks': tasks,
        'search_history': search_history
    })


@login_required
def update_task_view(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect('dashboard')


@login_required
def delete_task_view(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    task.delete()
    messages.success(request, "Задача удалена!")
    return redirect('dashboard')


@login_required
def favorites_view(request):
    favorite_cities = FavoriteCity.objects.filter(user=request.user).order_by('-added_at')

    if request.method == 'POST':
        city_name = request.POST.get('city_name', '').strip()
        if city_name:
            favorite, created = FavoriteCity.objects.get_or_create(
                user=request.user,
                city_name=city_name
            )
            if created:
                messages.success(request, f"Город {city_name} добавлен в избранное!")
            else:
                messages.info(request, f"Город {city_name} уже в избранном!")
            return redirect('home')
        else:
            messages.error(request, "Введите название города.")

    return render(request, 'dashboard/favorites.html', {
        'favorite_cities': favorite_cities
    })


@login_required
def remove_favorite_by_name(request):
    if request.method == 'POST':
        city_name = request.POST.get('city_name')
        if city_name:
            deleted_count = FavoriteCity.objects.filter(
                user=request.user,
                city_name=city_name
            ).delete()[0]
            if deleted_count > 0:
                messages.success(request, f"Город {city_name} удален из избранного!")
            return redirect('home')
    return redirect('favorites')


@login_required
def remove_favorite_view(request, city_id):
    favorite = get_object_or_404(FavoriteCity, id=city_id, user=request.user)
    city_name = favorite.city_name
    favorite.delete()
    messages.success(request, f"Город {city_name} удален из избранного!")
    return redirect('favorites')


@login_required
def settings_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = LanguageForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Настройки сохранены!")
            return redirect('settings')
    else:
        form = LanguageForm(instance=profile)

    return render(request, 'dashboard/settings.html', {'form': form})