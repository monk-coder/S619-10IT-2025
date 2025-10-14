from django.contrib import admin
from .models import UserNote, City, WeatherData


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'content', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'content')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'latitude', 'longitude')
    list_filter = ('country',)
    search_fields = ('name', 'country')
    ordering = ('name',)


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ('city', 'temperature', 'description', 'timestamp')
    list_filter = ('timestamp', 'city')
    search_fields = ('city__name', 'description')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Погодные данные', {
            'fields': ('city', 'temperature', 'description', 'humidity', 'wind_speed')
        }),
        ('Временные метки', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )


admin.site.site_header = "WeatherFlow Administration"
admin.site.site_title = "WeatherFlow Admin"
admin.site.index_title = "Панель управления WeatherFlow"