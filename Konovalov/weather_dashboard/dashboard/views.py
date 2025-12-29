from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import logging

from .models import SearchHistory, WeatherTask
from .weather_service import get_weather_data
from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)

def home(request):
    weather_data = None
    error = None
    
    if request.method == 'POST' and 'city' in request.POST:
        city = request.POST['city']
        logger.info(f"Пользователь {request.user.username if request.user.is_authenticated else 'неавторизованный'} ищет погоду для: {city}")
        
        weather_data = get_weather_data(city)
        
        if weather_data:
            if request.user.is_authenticated:
                try:
                    SearchHistory.objects.create(user=request.user, city=city)
                    logger.info(f"История поиска сохранена для пользователя {request.user.username}")
                except Exception as e:
                    logger.error(f"Ошибка при сохранении истории поиска: {str(e)}")
            
            messages.success(request, f'Погода для {city} загружена!')
        else:
            error = f"Не удалось получить данные для города '{city}'. Проверьте название города или попробуйте позже."
            messages.error(request, error)
            logger.warning(f"Не удалось получить погоду для города: {city}")
    
    context = {
        'weather_data': weather_data,
        'error': error,
    }
    
    if request.user.is_authenticated:
        try:
            context['tasks'] = WeatherTask.objects.filter(user=request.user)
            context['history'] = SearchHistory.objects.filter(user=request.user)[:10]
            context['tasks_count'] = WeatherTask.objects.filter(user=request.user).count()
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователя: {str(e)}")
            messages.error(request, 'Произошла ошибка при загрузке данных')
    
    return render(request, 'dashboard/home.html', context)

def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже авторизованы')
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Регистрация прошла успешно!')
                logger.info(f"Новый пользователь зарегистрирован: {user.username}")
                return redirect('home')
            except Exception as e:
                logger.error(f"Ошибка при регистрации пользователя: {str(e)}")
                messages.error(request, 'Произошла ошибка при регистрации')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
            logger.warning(f"Ошибки в форме регистрации: {form.errors}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'dashboard/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже авторизованы')
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Добро пожаловать, {username}!')
                    logger.info(f"Пользователь вошел в систему: {username}")
                    return redirect('home')
                else:
                    messages.error(request, 'Неверное имя пользователя или пароль')
            except Exception as e:
                logger.error(f"Ошибка при входе пользователя: {str(e)}")
                messages.error(request, 'Произошла ошибка при входе в систему')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = AuthenticationForm()
    
    return render(request, 'dashboard/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, 'Вы успешно вышли из системы.')
        logger.info(f"Пользователь вышел из системы: {username}")
    else:
        messages.info(request, 'Вы не были авторизованы.')
    
    return redirect('home')

@login_required
def create_task(request):
    try:
        if request.method == 'POST':
            city = request.POST.get('city', '').strip()
            task_text = request.POST.get('task_text', '').strip()
            
            if city and task_text:
                WeatherTask.objects.create(user=request.user, city=city, task_text=task_text)
                messages.success(request, 'Задача успешно создана!')
                logger.info(f"Создана задача для пользователя {request.user.username}: {city}")
            else:
                messages.error(request, 'Пожалуйста, заполните все поля.')
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {str(e)}")
        messages.error(request, 'Произошла ошибка при создании задачи.')
    
    return redirect('home')

@login_required
def update_task(request, task_id):
    try:
        task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
        
        if request.method == 'POST':
            city = request.POST.get('city', '').strip()
            task_text = request.POST.get('task_text', '').strip()
            
            if city and task_text:
                task.city = city
                task.task_text = task_text
                task.save()
                messages.success(request, 'Задача обновлена!')
                logger.info(f"Обновлена задача {task_id} для пользователя {request.user.username}")
            else:
                messages.error(request, 'Пожалуйста, заполните все поля.')
    except Exception as e:
        logger.error(f"Ошибка при обновлении задачи: {str(e)}")
        messages.error(request, 'Произошла ошибка при обновлении задачи.')
    
    return redirect('home')

@login_required
def delete_task(request, task_id):
    try:
        task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
        
        if request.method == 'POST':
            task.delete()
            messages.success(request, 'Задача удалена!')
            logger.info(f"Удалена задача {task_id} для пользователя {request.user.username}")
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи: {str(e)}")
        messages.error(request, 'Произошла ошибка при удалении задачи.')
    
    return redirect('home')

@login_required
def clear_history(request):
    try:
        if request.method == 'POST':
            count, _ = SearchHistory.objects.filter(user=request.user).delete()
            messages.success(request, f'История поиска очищена! Удалено {count} записей.')
            logger.info(f"Очищена история поиска для пользователя {request.user.username}: {count} записей")
    except Exception as e:
        logger.error(f"Ошибка при очистке истории: {str(e)}")
        messages.error(request, 'Произошла ошибка при очистке истории поиска.')
    
    return redirect('home')

def api_weather(request, city):
    """API endpoint для получения погоды"""
    try:
        weather_data = get_weather_data(city)
        if weather_data:
            return JsonResponse(weather_data)
        else:
            return JsonResponse({'error': 'City not found'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка в API для города {city}: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)