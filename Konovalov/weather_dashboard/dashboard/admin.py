from django.contrib import admin
from .models import SearchHistory, WeatherTask, WeatherCache

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'city', 'searched_at']
    list_filter = ['searched_at', 'user']
    search_fields = ['city', 'user__username']
    list_per_page = 20
    date_hierarchy = 'searched_at'

@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'city', 'task_text_preview', 'created_at', 'updated_at']
    list_filter = ['created_at', 'user', 'updated_at']
    search_fields = ['city', 'task_text', 'user__username']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    def task_text_preview(self, obj):
        if len(obj.task_text) > 50:
            return obj.task_text[:50] + '...'
        return obj.task_text
    task_text_preview.short_description = 'Задача'

@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ['id', 'city', 'last_updated', 'is_valid_cache']
    list_filter = ['last_updated']
    search_fields = ['city']
    readonly_fields = ['last_updated', 'weather_data_preview']
    list_per_page = 20
    
    def is_valid_cache(self, obj):
        return obj.is_valid()
    is_valid_cache.boolean = True
    is_valid_cache.short_description = 'Валиден'
    
    def weather_data_preview(self, obj):
        import json
        return json.dumps(obj.weather_data, ensure_ascii=False, indent=2)
    weather_data_preview.short_description = 'Данные погоды'