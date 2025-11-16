from .models import UserProfile

<<<<<<< HEAD

def user_settings(request):
    """Добавляет настройки пользователя в контекст всех шаблонов"""
    language = 'ru'
=======
def user_settings(request):
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
    theme = 'light'

    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
<<<<<<< HEAD
            language = profile.language
=======
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
            theme = profile.theme
        except UserProfile.DoesNotExist:
            pass

    return {
<<<<<<< HEAD
        'user_language': language,
        'user_theme': theme,
        'LANGUAGE': language,  # Добавляем для простоты
    }
=======
        'user_theme': theme,
    }
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
