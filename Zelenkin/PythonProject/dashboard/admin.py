from django.contrib import admin
from django.utils.html import format_html
from .models import CitySearchHistory, WeatherTask, WeatherCache


@admin.register(CitySearchHistory)
class CitySearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'city_name', 'country', 'searched_at']
    list_filter = ['searched_at', 'user', 'country']
    search_fields = ['city_name', 'user__username']
    readonly_fields = ['searched_at']
    date_hierarchy = 'searched_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'city', 'get_task_type_display',
        'is_completed', 'created_at', 'updated_at'
    ]
    list_filter = [
        'task_type', 'is_completed', 'created_at', 'updated_at', 'user'
    ]
    search_fields = ['title', 'description', 'city', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_completed']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def get_task_type_display(self, obj):
        return obj.get_task_type_display()

    get_task_type_display.short_description = 'Тип задачи'


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = [
        'city_name', 'country', 'temperature', 'humidity',
        'description', 'is_expired_display', 'cached_at'
    ]
    list_filter = ['cached_at', 'country']
    search_fields = ['city_name', 'country', 'description']
    readonly_fields = ['cached_at', 'weather_data_preview']
    date_hierarchy = 'cached_at'

    def is_expired_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">● Устарел</span>')
        return format_html('<span style="color: green;">● Актуален</span>')

    is_expired_display.short_description = 'Статус'

    def weather_data_preview(self, obj):
        return format_html('<pre>{}</pre>', str(obj.weather_data)[:500])

    weather_data_preview.short_description = 'Данные погоды (превью)'


admin.site.site_header = "Панель управления Погодным Дашбордом"
admin.site.site_title = "Погодный Дашборд"
admin.site.index_title = "Управление данными"