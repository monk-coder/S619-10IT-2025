import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserNote
from .forms import NoteForm

# Введите сюда ваш API ключ
API_KEY = 'de0ba8afcd2606f2eccf6c212abe0906'


def home(request):
    context = {}
    # Обработка поиска города
    if request.method == 'POST' and 'city' in request.POST:
        city = request.POST.get('city')
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            temperature = data['main']['temp']
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            forecast = f'{description.capitalize()}, {temperature}°C'
            context['humidity'] = humidity
        else:
            forecast = 'Город не найден или произошла ошибка API.'

        context['forecast'] = forecast
        context['city'] = city

        # Работа с историей поиска
        search_history = request.session.get('search_history', [])
        if city not in search_history:
            search_history.append(city)
        request.session['search_history'] = search_history

    # Получение истории поиска из сессии
    context['search_history'] = request.session.get('search_history', [])

    return render(request, 'forecast/home.html', context)


def clear_search_history(request):
    """Очистка истории поиска"""
    if 'search_history' in request.session:
        del request.session['search_history']
        messages.success(request, 'История поиска успешно очищена!')
    else:
        messages.info(request, 'История поиска уже пуста.')

    return redirect('home')


def remove_search_item(request, city_name):
    """Удаление конкретного города из истории поиска"""
    search_history = request.session.get('search_history', [])

    if city_name in search_history:
        search_history.remove(city_name)
        request.session['search_history'] = search_history
        request.session.modified = True
        messages.success(request, f'Город "{city_name}" удален из истории поиска!')
    else:
        messages.error(request, 'Город не найден в истории поиска.')

    return redirect('home')


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'forecast/register.html', {'form': form})


def user_login(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('home')

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
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()

    return render(request, 'forecast/login.html', {'form': form})


# --- VIEW ДЛЯ ЗАМЕТОК ---

@login_required
def note_list(request):
    """Список всех заметок пользователя"""
    notes = UserNote.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'forecast/note_list.html', {'notes': notes})


@login_required
def note_create(request):
    """Создание новой заметки"""
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            messages.success(request, 'Заметка успешно создана!')
            return redirect('note_list')
    else:
        form = NoteForm()
    return render(request, 'forecast/note_form.html', {'form': form, 'title': 'Создать заметку'})


@login_required
def note_edit(request, pk):
    """Редактирование существующей заметки"""
    note = get_object_or_404(UserNote, pk=pk, user=request.user)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заметка успешно обновлена!')
            return redirect('note_list')
    else:
        form = NoteForm(instance=note)
    return render(request, 'forecast/note_form.html', {'form': form, 'title': 'Редактировать заметку'})


@login_required
def note_delete(request, pk):
    """Удаление заметки"""
    note = get_object_or_404(UserNote, pk=pk, user=request.user)

    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Заметка успешно удалена!')
        return redirect('note_list')

    return render(request, 'forecast/note_confirm_delete.html', {'note': note})