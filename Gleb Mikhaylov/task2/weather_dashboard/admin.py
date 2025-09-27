from django.contrib import admin
from .models import WeatherTask, SearchHistory, WeatherCache


@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'city', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('title', 'description', 'city', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'searched_at')
    list_filter = ('searched_at', 'country')
    search_fields = ('city', 'user__username')
    readonly_fields = ('searched_at',)
    ordering = ('-searched_at',)


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ('city', 'country', 'temperature', 'humidity', 'cached_at')
    list_filter = ('cached_at', 'country')
    search_fields = ('city',)
    readonly_fields = ('cached_at',)
    ordering = ('-cached_at',)
