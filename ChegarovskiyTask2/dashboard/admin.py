from django.contrib import admin
<<<<<<< HEAD

# Register your models here.
=======
from .models import WeatherTask, FavoriteCity, CitySearchHistory, UserProfile, WeatherCache

# Регистрируем модели для админ-панели
@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'city_name', 'task_text', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at', 'user']
    search_fields = ['city_name', 'task_text']

@admin.register(FavoriteCity)
class FavoriteCityAdmin(admin.ModelAdmin):
    list_display = ['user', 'city_name', 'added_at']
    list_filter = ['added_at', 'user']
    search_fields = ['city_name']

@admin.register(CitySearchHistory)
class CitySearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'city_name', 'searched_at']
    list_filter = ['searched_at', 'user']
    search_fields = ['city_name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'language', 'theme']
    list_filter = ['language', 'theme']

@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ['city_name', 'cached_at']
    list_filter = ['cached_at']
    search_fields = ['city_name']
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
