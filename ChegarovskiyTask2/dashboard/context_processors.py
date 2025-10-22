from .models import UserProfile

def user_settings(request):
    theme = 'light'

    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            theme = profile.theme
        except UserProfile.DoesNotExist:
            pass

    return {
        'user_theme': theme,
    }
