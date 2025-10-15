from django.utils.translation import gettext_lazy as _
from .models import UserProfile


def get_user_language(request):
    """Получает язык пользователя"""
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return profile.language
        except UserProfile.DoesNotExist:
            return 'ru'
    return 'ru'


def translate_text(text, language):
    """Простая система перевода"""
    translations = {
        'Погодный Дашборд': {
            'en': 'Weather Dashboard'
        },
        'Мой кабинет': {
            'en': 'My Dashboard'
        },
        'Избранные города': {
            'en': 'Favorite Cities'
        },
        'Настройки': {
            'en': 'Settings'
        },
        'Выйти': {
            'en': 'Logout'
        },
        'Войти': {
            'en': 'Login'
        },
        'Регистрация': {
            'en': 'Register'
        },
        'Добавить новую задачу': {
            'en': 'Add New Task'
        },
        'Город': {
            'en': 'City'
        },
        'Задача': {
            'en': 'Task'
        },
        'Добавить задачу': {
            'en': 'Add Task'
        },
        'История поиска': {
            'en': 'Search History'
        },
        'Вы еще не искали погоду.': {
            'en': 'You haven\'t searched for weather yet.'
        },
        'Мои задачи': {
            'en': 'My Tasks'
        },
        'У вас пока нет задач.': {
            'en': 'You don\'t have any tasks yet.'
        },
        'Вернуть': {
            'en': 'Restore'
        },
        'Выполнено': {
            'en': 'Complete'
        },
        'Удалить': {
            'en': 'Delete'
        },
    }

    if text in translations and language in translations[text]:
        return translations[text][language]
    return text