from django.contrib import admin
from .models import SearchHistory, WeatherTask, WeatherCache

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'searched_at']
    list_filter = ['searched_at', 'user']
    search_fields = ['city', 'user__username']

@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'task_text', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['city', 'task_text', 'user__username']

@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ['city', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['city']
    readonly_fields = ['last_updated']