from django.contrib import admin
from .models import WeatherTask, CitySearchHistory


@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'related_city', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at', 'user']
    search_fields = ['title', 'description', 'related_city']
    list_editable = ['is_completed']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'description', 'related_city')
        }),
        ('Статус', {
            'fields': ('is_completed',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CitySearchHistory)
class CitySearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['city_name', 'country', 'user', 'searched_at']
    list_filter = ['searched_at', 'user']
    search_fields = ['city_name', 'country']
    readonly_fields = ['searched_at']

    fieldsets = (
        ('Информация о поиске', {
            'fields': ('user', 'city_name', 'country')
        }),
        ('Дата и время', {
            'fields': ('searched_at',)
        }),
    )