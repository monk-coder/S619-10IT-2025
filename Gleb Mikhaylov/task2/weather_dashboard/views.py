from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .models import WeatherTask, SearchHistory
from .forms import CustomUserCreationForm, WeatherTaskForm, WeatherSearchForm
from .services import WeatherService, WeatherAPIException
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Главная страница с поиском погоды"""
    weather_data = None
    search_form = WeatherSearchForm()
    
    if request.method == 'POST':
        logger.info(f"Получен POST запрос: {request.POST}")
        search_form = WeatherSearchForm(request.POST)
        if search_form.is_valid():
            city = search_form.cleaned_data['city']
            logger.info(f"Поиск погоды для города: {city}")
            try:
                weather_service = WeatherService()
                weather_data = weather_service.get_weather(city)
                logger.info(f"Получены данные погоды: {weather_data}")
                
                # Сохраняем в историю поиска для аутентифицированных пользователей
                if request.user.is_authenticated:
                    SearchHistory.objects.update_or_create(
                        user=request.user,
                        city=city,
                        defaults={'country': weather_data.get('country', '')}
                    )
                    
            except WeatherAPIException as e:
                logger.error(f"Ошибка API погоды: {str(e)}")
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {str(e)}")
                messages.error(request, "Произошла неожиданная ошибка. Попробуйте позже.")
        else:
            logger.error(f"Форма невалидна: {search_form.errors}")
            messages.error(request, "Пожалуйста, введите название города.")
    
    # Получаем последние задачи пользователя
    user_tasks = []
    if request.user.is_authenticated:
        user_tasks = WeatherTask.objects.filter(user=request.user)[:5]
    
    context = {
        'weather_data': weather_data,
        'search_form': search_form,
        'user_tasks': user_tasks,
    }
    return render(request, 'weather_dashboard/home.html', context)


def register_view(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'weather_dashboard/register.html', {'form': form})


def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    
    return render(request, 'weather_dashboard/login.html')


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('home')


@login_required
def tasks_list(request):
    """Список задач пользователя"""
    tasks = WeatherTask.objects.filter(user=request.user)
    
    # Фильтрация
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Пагинация
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'priority_filter': priority_filter,
        'status_filter': status_filter,
    }
    return render(request, 'weather_dashboard/tasks_list.html', context)


@login_required
def task_create(request):
    """Создание новой задачи"""
    if request.method == 'POST':
        form = WeatherTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Задача успешно создана!')
            return redirect('tasks_list')
    else:
        form = WeatherTaskForm()
    
    return render(request, 'weather_dashboard/task_form.html', {'form': form, 'title': 'Создать задачу'})


@login_required
def task_edit(request, task_id):
    """Редактирование задачи"""
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = WeatherTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно обновлена!')
            return redirect('tasks_list')
    else:
        form = WeatherTaskForm(instance=task)
    
    return render(request, 'weather_dashboard/task_form.html', {
        'form': form, 
        'title': 'Редактировать задачу',
        'task': task
    })


@login_required
def task_delete(request, task_id):
    """Удаление задачи"""
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача успешно удалена!')
        return redirect('tasks_list')
    
    return render(request, 'weather_dashboard/task_confirm_delete.html', {'task': task})


@login_required
def task_detail(request, task_id):
    """Детальный просмотр задачи"""
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    return render(request, 'weather_dashboard/task_detail.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def task_update_status(request, task_id):
    """Обновление статуса задачи через AJAX"""
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)
    new_status = request.POST.get('status')
    
    if new_status in [choice[0] for choice in WeatherTask.STATUS_CHOICES]:
        task.status = new_status
        task.save()
        return JsonResponse({'success': True, 'status': task.get_status_display()})
    
    return JsonResponse({'success': False, 'error': 'Неверный статус'})


@login_required
def search_history(request):
    """История поиска пользователя"""
    history = SearchHistory.objects.filter(user=request.user)
    
    # Пагинация
    paginator = Paginator(history, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'weather_dashboard/search_history.html', {'page_obj': page_obj})


@login_required
def dashboard(request):
    """Дашборд пользователя с общей статистикой"""
    user_tasks = WeatherTask.objects.filter(user=request.user)
    
    # Статистика задач
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='completed').count()
    pending_tasks = user_tasks.filter(status='pending').count()
    
    # Последние задачи
    recent_tasks = user_tasks[:5]
    
    # История поиска
    recent_searches = SearchHistory.objects.filter(user=request.user)[:10]
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'recent_tasks': recent_tasks,
        'recent_searches': recent_searches,
    }
    return render(request, 'weather_dashboard/dashboard.html', context)
