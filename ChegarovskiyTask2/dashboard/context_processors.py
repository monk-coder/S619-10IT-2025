from .models import UserProfile


def user_settings(request):
    """Добавляет настройки пользователя в контекст всех шаблонов"""
    language = 'ru'
    theme = 'light'

    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            language = profile.language
            theme = profile.theme
        except UserProfile.DoesNotExist:
            pass

    return {
        'user_language': language,
        'user_theme': theme,
        'LANGUAGE': language,  # Добавляем для простоты
    }