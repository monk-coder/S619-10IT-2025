from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
import random
from .models import UserProfile, SearchHistory, UserNote


def home(request):
    weather_data = None
    error = None

    if request.method == 'POST':
        city = request.POST.get('city', '').strip()

        if not city:
            error = "Аллах говорит:Введите название города"
        else:
            try:
                # ТВОЙ API КЛЮЧ
                api_key = "fa77f2b3447d3ec6c1f38b71c9c5da1c"
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"

                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    weather_data = {
                        'city': data['name'],
                        'country': data['sys']['country'],
                        'temperature': round(data['main']['temp']),
                        'feels_like': round(data['main']['feels_like']),
                        'description': data['weather'][0]['description'],
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'wind_speed': data['wind']['speed'],
                        'icon': data['weather'][0]['icon'],
                    }

                    # Сохраняем в историю если пользователь авторизован
                    if request.user.is_authenticated:
                        SearchHistory.objects.create(
                            user=request.user,
                            city=city,
                            temperature=weather_data['temperature'],
                            description=weather_data['description']
                        )

                elif response.status_code == 401:
                    error = "Ошибка API ключа. Используем тестовые данные."
                    weather_data = get_test_weather_data(city)

                elif response.status_code == 404:
                    error = f"Город '{city}' не найден. Попробуйте другое название."

                else:
                    error = f"Ошибка сервера ({response.status_code}). Используем тестовые данные."
                    weather_data = get_test_weather_data(city)

            except requests.exceptions.Timeout:
                error = "Таймаут запроса. Используем тестовые данные."
                weather_data = get_test_weather_data(city)

            except Exception as e:
                error = f"Ошибка подключения. Используем тестовые данные."
                weather_data = get_test_weather_data(city)

    # Функция для тестовых данных (резервный вариант)
    def get_test_weather_data(city):
        test_data = {
            'москва': {'name': 'Москва', 'country': 'RU', 'temp': 15, 'desc': 'облачно', 'icon': '04d'},
            'moscow': {'name': 'Moscow', 'country': 'RU', 'temp': 15, 'desc': 'cloudy', 'icon': '04d'},
            'санкт-петербург': {'name': 'Санкт-Петербург', 'country': 'RU', 'temp': 12, 'desc': 'дождь', 'icon': '10d'},
            'лондон': {'name': 'Лондон', 'country': 'GB', 'temp': 10, 'desc': 'туман', 'icon': '50d'},
            'london': {'name': 'London', 'country': 'GB', 'temp': 10, 'desc': 'fog', 'icon': '50d'},
        }

        city_lower = city.lower()
        if city_lower in test_data:
            data = test_data[city_lower]
            return {
                'city': data['name'],
                'country': data['country'],
                'temperature': data['temp'],
                'feels_like': data['temp'] - 2,
                'description': data['desc'],
                'humidity': random.randint(50, 90),
                'pressure': 1013,
                'wind_speed': round(random.uniform(2, 8), 1),
                'icon': data['icon'],
            }
        else:
            return {
                'city': city.title(),
                'country': '??',
                'temperature': random.randint(-10, 30),
                'feels_like': random.randint(-12, 28),
                'description': random.choice(['Аллах сказал что ясно', 'Аллах сказал что облачно', 'Аллах сказал что дождь', 'Аллах сказал что снег']),
                'humidity': random.randint(40, 80),
                'pressure': random.randint(980, 1030),
                'wind_speed': round(random.uniform(1, 15), 1),
                'icon': random.choice(['01d', '02d', '03d', '04d', '09d', '10d']),
            }

    popular_cities = ['Москва', 'Санкт-Петербург', 'Лондон', 'Нью-Йорк', 'Париж']

    context = {
        'weather_data': weather_data,
        'error': error,
        'popular_cities': popular_cities,
    }

    return render(request, 'weather/home.html', context)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                UserProfile.objects.create(user=user)
                login(request, user)
                messages.success(request, f'Аллах2.0 приветствует вас, {user.username}!')
                return redirect('weather_home')
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = UserCreationForm()

    return render(request, 'weather/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'С возвращением, {username}!')
                return redirect('weather_home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = AuthenticationForm()

    return render(request, 'weather/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('weather_home')


@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_notes = UserNote.objects.filter(user=request.user)
    search_history = SearchHistory.objects.filter(user=request.user)[:10]

    if request.method == 'POST':
        # Обработка любимого города
        favorite_city = request.POST.get('favorite_city', '')
        if favorite_city:
            user_profile.favorite_city = favorite_city
            user_profile.save()
            messages.success(request, 'Любимый город сохранен!')

        # Обработка новой заметки
        note_title = request.POST.get('note_title', '')
        note_content = request.POST.get('note_content', '')
        if note_title and note_content:
            UserNote.objects.create(
                user=request.user,
                title=note_title,
                content=note_content
            )
            messages.success(request, 'Аллах добавил заметку!')
            return redirect('profile')

    context = {
        'user_profile': user_profile,
        'user_notes': user_notes,
        'search_history': search_history,
    }
    return render(request, 'weather/profile.html', context)


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(UserNote, id=note_id, user=request.user)

    if request.method == 'POST':
        note.title = request.POST.get('title', '')
        note.content = request.POST.get('content', '')
        note.save()
        messages.success(request, 'Аллах обновил заметку!')
        return redirect('profile')

    return render(request, 'weather/edit_note.html', {'note': note})


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(UserNote, id=note_id, user=request.user)

    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Аллах удалил Заметку!')

    return redirect('profile')