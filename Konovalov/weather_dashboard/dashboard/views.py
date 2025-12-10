from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import SearchHistory, WeatherTask
from .weather_service import get_weather_data

def home(request):
    weather_data = None
    error = None
    
    if request.method == 'POST' and 'city' in request.POST:
        city = request.POST['city']
        print(f"🔍 Пользователь ищет погоду для: {city}")
        
        weather_data = get_weather_data(city)
        
        if weather_data:
            if request.user.is_authenticated:
                SearchHistory.objects.create(user=request.user, city=city)
            messages.success(request, f'Погода для {city} загружена!')
        else:
            error = f"Не удалось получить данные для города '{city}'. Проверьте название города или попробуйте позже."
            messages.error(request, error)
    
    context = {
        'weather_data': weather_data,
        'error': error,
    }
    
    if request.user.is_authenticated:
        context['tasks'] = WeatherTask.objects.filter(user=request.user)
        context['history'] = SearchHistory.objects.filter(user=request.user)[:10]
        context['tasks_count'] = WeatherTask.objects.filter(user=request.user).count()
    
    return render(request, 'dashboard/home.html', context)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
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
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'dashboard/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('home')

@login_required
def create_task(request):
    if request.method == 'POST':
        city = request.POST.get('city')
        task_text = request.POST.get('task_text')
        if city and task_text:
            WeatherTask.objects.create(user=request.user, city=city, task_text=task_text)
            messages.success(request, 'Задача успешно создана!')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля.')
    return redirect('home')

@login_required
def update_task(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    if request.method == 'POST':
        task.city = request.POST.get('city', task.city)
        task.task_text = request.POST.get('task_text', task.task_text)
        task.save()
        messages.success(request, 'Задача обновлена!')
    return redirect('home')

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача удалена!')
    return redirect('home')

@login_required
def clear_history(request):
    if request.method == 'POST':
        SearchHistory.objects.filter(user=request.user).delete()
        messages.success(request, 'История поиска очищена!')
    return redirect('home')

def api_weather(request, city):
    """API endpoint для получения погоды"""
    weather_data = get_weather_data(city)
    if weather_data:
        return JsonResponse(weather_data)
    else:
        return JsonResponse({'error': 'City not found'}, status=404)